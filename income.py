import json
import requests
from web3 import Web3

CHAINS_WEB3 = {'moonbeam': Web3(
    Web3.HTTPProvider('https://rpc.api.moonbeam.network')),
    # 'bsc': Web3(
    # Web3.HTTPProvider('https://bsc-dataseed.binance.org')),
    # 'polygon': Web3(
    # Web3.HTTPProvider('https://polygon-rpc.com')),
    # 'avax': Web3(
    # Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc')),
}


# set
STRATEGIST = "0xc75E1B127E288f1a33606a52AB5C91BBe64EaAfe"


BASE_URL = "https://api.beefy.finance/"

income = {'moonbeam': [], 'polygon': [], 'avax': [], 'bsc': []}

VAULTS = requests.get(BASE_URL + "vaults").json()
#filter VAULTS by status
VAULTS = [vault for vault in VAULTS if vault['status'] == 'active']

APY = requests.get(BASE_URL + "apy/breakdown").json()
TVL = requests.get(BASE_URL + "tvl").json()

# load ABI as json from file ABI.json using absolute path
with open('/home/lodelux/projects/income/ABI.json') as f:
    ABI = json.load(f)


def getTvl(id):
    for index, batch in TVL.items():
        try:
            return batch[id]
        except:
            continue
    return 0


def main():
    for i, vault in enumerate(VAULTS):
        print("\r{}/{}".format(i, len(VAULTS)), end="")
        try:
            web3 = CHAINS_WEB3[vault['chain']]
            contract = web3.eth.contract(address=vault['strategy'], abi=ABI)
            _strategist = contract.functions.strategist().call()
        except:
            continue

        if(_strategist == STRATEGIST):
            income[vault['chain']].append([vault['id']])

    total = 0
    for chain, vaults in income.items():
        print(chain + ': \n\n')
        totalChain = 0
        for vault in vaults:
            vault_tvl = getTvl(vault[0])
            vault_income = round(
                APY[vault[0]]['vaultApr'] * vault_tvl * 0.005, 2)
            vault.append(vault_income)
            print(
                f'{vault[0]} - [{round(vault_tvl /1000,2)}k$ at {round(APY[vault[0]]["vaultApr"]*100,2)}%] -{round(vault[1] / 365,2)}$/day | {round(vault[1]/12,2)}$/month | {round(vault[1],2)}$/year \n')
            totalChain += vault_income

        total += totalChain

        print(
            f'\ntotal for {chain}: {round(totalChain / 365,2)}$/day | {round(totalChain/12,2)}$/month | {round(totalChain,2)}$/year \n\n')

    print(
        f'total all chains: {round(total / 365,2)}$/day | {round(total/12,2)}$/month | {round(total,2)}$/year \n')



    


main()
