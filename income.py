import json
import requests
import os
from web3 import Web3

CHAINS_WEB3 = {'moonbeam': Web3(
    Web3.HTTPProvider('https://rpc.api.moonbeam.network')),
    'bsc': Web3(
    Web3.HTTPProvider('https://bsc-dataseed.binance.org')),
    'polygon': Web3(
    Web3.HTTPProvider('https://polygon-rpc.com')),
    'avax': Web3(
    Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc')),
}


#set 
STRATEGIST = "0xc75E1B127E288f1a33606a52AB5C91BBe64EaAfe"


BASE_URL = "https://api.beefy.finance/"

#add the chains that you want to track
income = {'moonbeam': [], 'polygon': [], 'avax': [], 'bsc': []}

APY = requests.get(BASE_URL + "apy/breakdown").json()
TVL = requests.get(BASE_URL + "tvl").json()

""" load ABI as json from file ABI.json using absolute path"""
with open('/home/lodelux/projects/income/ABI.json') as f:
    ABI = json.load(f)

""" fetch vaults"""
def getVaults():
    try:
        vaults = requests.get(BASE_URL + "vaults").json()
        return vaults
    except:
        print("error in fetching vaults")
        return []


""" get tvl for vault id, note that api returns batch of vaults, so we need to find the correct one"""
def getTvl(id):
    for index, batch in TVL.items():
        try:
            return batch[id]
        except:
            continue
    return 0


""" save  vaults to file"""
def saveVaults(vaults):
    with open('/home/lodelux/projects/income/vaults.json', 'w') as f:
        json.dump(vaults, f)


""" filter vaults by strategist using web3"""
def filterVaultsByStrategist(vaults):
    for i, vault in enumerate(vaults):
        print("\r{}/{}".format(i, len(vaults)), end="")
        try:
            web3 = CHAINS_WEB3[vault['chain']]
            vault['strategist'] = web3.eth.contract(
                abi=ABI, address=vault['strategy']).functions.strategist().call()
        except Exception as e:
            continue
    _vaults = [
        vault for vault in vaults if 'strategist' in vault and vault['strategist'] == STRATEGIST]
    #clear console
    print("\r" + " " * 50)
    saveVaults(_vaults)
    return _vaults


""" add apy to VAULTS from APY"""
def addApy(vaults):
    for vault in vaults:
        try:
            vault['apy'] = APY[vault['id']]['vaultApr']
        except Exception as e:
            print(f'error in adding apy for {vault["id"]} : {e}')
            continue
    return vaults


""" add tvl to VAULTS from TVL"""
def addTvl(vaults):
    for vault in vaults:
        try:
            vault['tvl'] = getTvl(vault['id'])
        except:
            print(f'error in adding tvl for {vault["id"]}')
            continue
    return vaults


""" add income to VAULTS"""
def addIncome(vaults):
    for vault in vaults:
        try:
            vault['income'] = round(vault['apy'] * vault['tvl'] * 0.005, 2)
        except:
            print(f'error in adding income for {vault["id"]}')
            continue
    return vaults


"""  divide vaults by chain"""
def divideVaultsByChain(vaults):
    for chain in CHAINS_WEB3:
        income[chain] = [vault for vault in vaults if vault['chain'] == chain]
    return income


""" print income in a table format"""
def printIncome(income):
    print('\n\n')
    total = 0
    totalTvl = 0
    for chain, vaults in income.items():
        print('-' * 87)
        print('|{:^30}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|'.format(
            'id', 'tvl (k$)', 'apy (%)', 'day ($)', 'week ($)', 'month ($)'))
        print('-' * 87)
        totalChain = 0
        totalTvlChain = 0
        for vault in vaults:
            print('|{:^30}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|\n'.format(
                vault['id'], round(vault['tvl'] / 1000, 2), round(vault['apy'] * 100, 2), round(vault['income'] / 365, 2), round(vault['income'] / 52, 2), round(vault['income'] / 12, 2)))
            totalChain += vault['income']

        totalTvlChain = sum([vault['tvl'] for vault in vaults])
        print('-' * 87)
        print('|{:^30}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|'.format(
            'total ' + chain.upper(), round(totalTvlChain / 1000, 2), '', round(totalChain / 365, 2), round(totalChain / 52, 2), round(totalChain / 12, 2)))
        print('-' * 87)

        print('\n')
        total += totalChain
        totalTvl += totalTvlChain

    print('-' * 87)
    print('|{:^30}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|'.format(
        'id', 'tvl (k$)', 'apy (%)', 'day ($)', 'week ($)', 'month ($)'))
    print('-' * 87)
    print('|{:^30}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|'.format(
        'total ALL CHAINS', round(totalTvl / 1000, 2), '', round(total / 365, 2), round(total / 52, 2), round(total / 12, 2)))
    print('-' * 87)


""" save income for testing purposes"""
def saveIncome(income):
    with open('/home/lodelux/projects/income/income.json', 'w') as f:

        json.dump(income, f)


""" test printIncome using income.json"""
def testPrintIncome():
    with open('/home/lodelux/projects/income/income.json') as f:
        income = json.load(f)
    printIncome(income)


def main(vaults, choice):
    if choice != str(1):
        vaults = [vault for vault in vaults if vault['status'] == 'active']
        vaults = filterVaultsByStrategist(vaults)
    vaults = addApy(vaults)
    vaults = addTvl(vaults)
    vaults = addIncome(vaults)
    income = divideVaultsByChain(vaults)
    printIncome(income)


if __name__ == '__main__':
    #let user choose if to use stored vaults or fetch new ones
    print('1 to use stored vaults, 2 to fetch new ones')
    choice = input()
    if choice == '1' and os.path.exists('/home/lodelux/projects/income/vaults.json'):
        with open('/home/lodelux/projects/income/vaults.json') as f:
            vaults = json.load(f)
    else:
        vaults = getVaults()
    main(vaults, choice)
