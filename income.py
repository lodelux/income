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


# set
STRATEGIST = "0xc75E1B127E288f1a33606a52AB5C91BBe64EaAfe"


BASE_URL = "https://api.beefy.finance/"
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
# add the chains that you want to track
income = {'moonbeam': [], 'polygon': [], 'avax': [], 'bsc': []}

APY = requests.get(BASE_URL + "apy/breakdown").json()
TVL = requests.get(BASE_URL + "tvl").json()

# load ABI as json from file ABI.json using absolute path
with open('/home/lodelux/projects/income/ABI.json') as f:
    ABI = json.load(f)


def getVaults():
    """
    It fetches all the vaults from the API and returns them as a list
    :return: A list of dictionaries
    """
    try:
        vaults = requests.get(BASE_URL + "vaults").json()
        return vaults
    except:
        print("error in fetching vaults")
        return []


def getTvl(id):
    """
    It returns the TVL for a given vault ID.
    note that api returns batch of vaults, so we need to find the correct one
    :param id: vault id
    :return: A list of dictionaries, each dictionary is a vault
    """
    for index, batch in TVL.items():
        try:
            return batch[id]
        except:
            continue
    return 0


def saveVaults(vaults):
    """
    > save  vaults to file

    :param vaults: a list of dictionaries, each dictionary is a vault
    """
    with open(BASE_PATH + '/vaults.json', 'w') as f:
        json.dump(vaults, f)


def filterVaultsByStrategist(vaults):
    """
    It filters vaults by strategist using web3

    :param vaults: list of vaults
    :return: A list of vaults that have the strategist address
    """
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
    # clear console
    print("\r" + " " * 50)
    saveVaults(_vaults)
    return _vaults


def addApy(vaults):
    """
    It takes a list of dictionaries, and for each dictionary, it adds a new key-value pair to the
    dictionary. 

    The key is 'apy' and the value is the value of the key 'vaultApr' in the dictionary in the list APY
    whose key 'id' is the same as the value of the key 'id' in the dictionary in the list VAULTS. 

    If there is no such dictionary in APY, it prints an error message.

    :param vaults: list of vaults
    :return: A list of dictionaries.
    """
    for vault in vaults:
        try:
            vault['apy'] = APY[vault['id']]['vaultApr']
        except Exception as e:
            print(f'error in adding apy for {vault["id"]} : {e}')
            continue
    return vaults


def addTvl(vaults):
    """
    It takes a list of dictionaries, and for each dictionary in the list, it adds a new key-value pair
    to the dictionary. namely it adds 'tvl'

    :param vaults: list of vaults
    :return: A list of dictionaries.
    """
    for vault in vaults:
        try:
            vault['tvl'] = getTvl(vault['id'])
        except:
            print(f'error in adding tvl for {vault["id"]}')
            continue
    return vaults


def addIncome(vaults):
    """
    For each vault in the list of vaults, add a new key-value pair to the vault dictionary, where the
    key is 'income' and the value is the product of the vault's APY and TVL and the strategist fee (0.005), rounded to two decimal
    places

    :param vaults: list of dicts, each dict is a vault
    :return: A list of dictionaries
    """
    for vault in vaults:
        try:
            vault['income'] = round(vault['apy'] * vault['tvl'] * 0.005, 2)
        except:
            print(f'error in adding income for {vault["id"]}')
            continue
    return vaults


def divideVaultsByChain(vaults):
    """
    It takes a list of vaults and returns a dictionary of vaults divided by chain.

    :param vaults: list of vaults
    """
    for chain in CHAINS_WEB3:
        income[chain] = [vault for vault in vaults if vault['chain'] == chain]
    return income


def printIncome(income):
    """
    It takes a dictionary of dictionaries, and prints it in a table format

    :param income: a dictionary of income for each chain
    """
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


def saveIncome(income):
    """
    It saves the income data to a file (used for testing purposes)

    :param income: a dictionary of income for each chain
    """
    with open(BASE_PATH + '/income.json', 'w') as f:
        json.dump(income, f)


def testPrintIncome():
    """ test printIncome using income.json"""
    with open('/home/lodelux/projects/income/income.json') as f:
        income = json.load(f)
    printIncome(income)


def main(vaults, choice):
    """
    It takes a list of vaults, filters them by status and strategist, adds APY, TVL, and income, then
    divides them by chain and prints the income.

    :param vaults: a list of dictionaries, each dictionary representing a vault
    :param choice: 1 = cached vaults, 2 = fetch  vaults from api 
    """
    if choice != str(1):
        vaults = [vault for vault in vaults if vault['status'] == 'active']
        vaults = filterVaultsByStrategist(vaults)
    vaults = addApy(vaults)
    vaults = addTvl(vaults)
    vaults = addIncome(vaults)
    income = divideVaultsByChain(vaults)
    printIncome(income)


if __name__ == '__main__':
    # let user choose if to use stored vaults or fetch new ones
    print('1 to use stored vaults, 2 to fetch new ones')
    choice = input()
    if choice == '1' and os.path.exists(BASE_PATH + '/vaults.json'):
        with open(BASE_PATH + '/vaults.json') as f:
            vaults = json.load(f)
    else:
        vaults = getVaults()
    main(vaults, choice)
