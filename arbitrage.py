from web3 import Web3
import json
import requests
import time

class BSC_Network:
    pancake_contract = None
    tau_contract = None
    usdc_contract = None
    router_address = None
    tau_lamdenbridge_contract = None
    tau_bridge_address = None
    bsc_rpc = 'https://bsc-dataseed.binance.org/'
    web3 = Web3(Web3.HTTPProvider(bsc_rpc))

    def __init__(self):
        pancake_abi_file = open('pancake_abi.json','r')
        pancake_abi = json.load(pancake_abi_file)
        self.router_address = self.web3.toChecksumAddress("0x10ED43C718714eb63d5aA57B78B54704E256024E")
        self.pancake_contract = self.web3.eth.contract(address=router_address, abi=pancake_abi)
        tau_abi_file = open('tau_abi.json','r')
        tau_abi = json.load(tau_abi_file)
        tau_address = self.web3.toChecksumAddress("0x70d7109d3afe13ee8f9015566272838519578c6b")
        self.tau_contract = self.web3.eth.contract(address=tau_address, abi=tau_abi)
        usdc_abi_file = open('usdc_abi.json','r')
        usdc_abi = json.load(usdc_abi_file)
        usdc_address = self.web3.toChecksumAddress("0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d")
        self.usdc_contract = self.web3.eth.contract(address=usdc_address, abi=usdc_abi)
        tau_bridge_abi_file = open('bridge_abi.json','r')
        tau_bridge_abi = json.load(tau_bridge_abi_file)
        self.tau_bridge_address = self.web3.toChecksumAddress("0x46e126489b7965ecc13e58f72f6d14b140614c18")
        self.tau_bridge_contract = self.web3.eth.contract(address=self.tau_bridge_address, abi=tau_bridge_abi)

    def getOutcomeBeforeSwap(self, pair, amount_in, swap_type):
        if(swap_type == "sell"):
            router_path = [self.web3.toChecksumAddress(pair["outputCurrency"]), self.web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"), self.web3.toChecksumAddress(pair["inputCurrency"])] # Input is TAU, Outcome is USDC
        elif(swap_type == "buy"):
            router_path = [self.web3.toChecksumAddress(pair["inputCurrency"]), self.web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"), self.web3.toChecksumAddress(pair["outputCurrency"])] # Input is USDC, Outcome is TAU
        amountsOut = self.pancake_contract.functions.getAmountsOut(self.web3.toWei(amount_in, 'ether'), router_path).call()
        return self.web3.fromWei(amountsOut[2], 'ether')

    def doSwap(self,wallet_address, private_key, pair, amount_in, swap_type):
        if(swap_type == "sell"):
            router_path = [self.web3.toChecksumAddress(pair["outputCurrency"]), self.web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"), self.web3.toChecksumAddress(pair["inputCurrency"])] # Input is TAU, Outcome is USDC
            self.tau_contract.approve(wallet_address, self.router_address, amount_in, private_key)

        if(swap_type == "buy"):
            router_path = [self.web3.toChecksumAddress(pair["inputCurrency"]), self.web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"), self.web3.toChecksumAddress(pair["outputCurrency"])] # Input is USDC, Outcome is TAU
            self.usdc_contract.approve(wallet_address, self.router_address, amount_in, private_key)

        nonce = self.web3.eth.get_transaction_count(wallet_address)
        txn = self.pancake_contract.functions.swapExactTokensForTokens(
            self.web3.toWei(amount_in, 'ether'),
            0, # here setup the minimum destination token you want to have, you can do some math, or you can put a 0 if you don't want to care
            router_path,
            wallet_address,
            (int(time.time()) + 1000000)
        ).buildTransaction({
            'from': wallet_address,
            #'gas': 260947,
            'gasPrice': self.web3.toWei('5','gwei'),
            'nonce': nonce,
        })
        signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.web3.toHex(tx_token)

    def doBridgeToLamden(self, wallet_address, private_key, amount, swap_type):
        if(swap_type == "sell"):
            self.usdc_contract.approve(wallet_address, self.bridge_address, amount, private_key)
            nonce = self.web3.eth.get_transaction_count(wallet_address)
            txn = self.bridge_contract.functions.deposit(
                self.web3.toHex(amount),
                "ff61544ea94eaaeb5df08ed863c4a938e9129aba6ceee5f31b6681bdede11b89"
            ).buildTransaction({
                'from': wallet_address,
                #'gas': 260947,
                'gasPrice': self.web3.toWei('5','gwei'),
                'nonce': nonce,
            })
            signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=private_key)
            tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            return self.web3.toHex(tx_token)

        if(swap_type == "buy"):
            self.tau_contract.approve(wallet_address, self.bridge_address, amount, private_key)
            nonce = self.web3.eth.get_transaction_count(wallet_address)
            txn = self.bridge_contract.functions.deposit(
                self.web3.toHex(amount),
                "ff61544ea94eaaeb5df08ed863c4a938e9129aba6ceee5f31b6681bdede11b89"
            ).buildTransaction({
                'from': wallet_address,
                #'gas': 260947,
                'gasPrice': self.web3.toWei('5','gwei'),
                'nonce': nonce,
            })
            signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=private_key)
            tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            return self.web3.toHex(tx_token)

class Lamden_Network:
    endpoint = "https://blockservice.nebulamden.finance/current/all/con_rocketswap_official_v1_1"
    fee_percent = 0.005

    def getOutcomeBeforeSwap(self, amount_in, pair, swap_type):
        if(swap_type == "sell"):
            url = self.endpoint + "/reserves/" + pair
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
                
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            token_reserve = float(data["con_rocketswap_official_v1_1"]["reserves"][pair][1]["__fixed__"])
            currency_reserve = float(data["con_rocketswap_official_v1_1"]["reserves"][pair][0]["__fixed__"])

            k = currency_reserve * token_reserve
            new_currency_reserve = currency_reserve + amount_in
            new_token_reserve = k / new_currency_reserve
            tokens_purchased = token_reserve - new_token_reserve
            fee = tokens_purchased * self.fee_percent
            tokens_purchased = tokens_purchased - fee

            return tokens_purchased

        if(swap_type == "buy"):
            url = self.endpoint + "/reserves/" + pair
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
                
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            token_reserve = float(data["con_rocketswap_official_v1_1"]["reserves"][pair][1]["__fixed__"])
            currency_reserve = float(data["con_rocketswap_official_v1_1"]["reserves"][pair][0]["__fixed__"])

            k = currency_reserve * token_reserve
            new_token_reserve = token_reserve + amount_in
            new_currency_reserve = k / new_token_reserve
            currency_purchased = currency_reserve - new_currency_reserve
            fee = currency_purchased * self.fee_percent
            currency_purchased = currency_purchased - fee

            return currency_purchased




bsc = BSC_Network()
lamden = Lamden_Network()

while(True):
    time.sleep(2)

    bsc_buy_amount = bsc.getOutcomeBeforeSwap({"inputCurrency":"0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "outputCurrency": "0x70d7109D3AfE13EE8f9015566272838519578c6b"}, 100, "buy")
    lamden_sell = lamden.getOutcomeBeforeSwap(float(bsc_buy_amount), "con_lusd_lst001", "sell")

    if(lamden_sell > 103):
        print("Its worth to arbitrage now and buy TAU on Pancakeswap for 100 USDC and sell Outcome TAU on Rocketswap")

        bsc.doSwap(bsc.web3.toChecksumAddress("PUBKEY"), "PRIVKEY",{"inputCurrency":"0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "outputCurrency": "0x70d7109D3AfE13EE8f9015566272838519578c6b"}, 100, "buy")
        print(f"Outcome BSC Buy using 100 USDC getting TAU: {bsc_buy_amount}")


        #bridge from bsc to lamden and sell tau
        print(f"Outcome Lamden Sell {bsc_buy_amount} TAU getting USDC: {lamden_sell}")


    lamden_buy_amount = lamden.getOutcomeBeforeSwap(100, "con_lusd_lst001", "buy")
    bsc_sell_amount = bsc.getOutcomeBeforeSwap({"inputCurrency":"0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "outputCurrency": "0x70d7109D3AfE13EE8f9015566272838519578c6b"},float(lamden_buy_amount), "sell")

    if(bsc_sell_amount > 103):
        print("Its worth to arbitrage now and buy TAU on Rocketswap for 100 USDC and sell Outcome TAU on Pancakeswap")
        
        #buy on lamden and bridge tau to bsc
        print(f"Outcome Lamden Buy using 100 USDC getting TAU: {lamden_buy_amount}")

        bsc.doSwap(bsc.web3.toChecksumAddress("PUBKEY"), "PRIVKEY",{"inputCurrency":"0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "outputCurrency": "0x70d7109D3AfE13EE8f9015566272838519578c6b"}, MISSING_AMOUNT, "sell")
        print(f"Outcome BSC Sell {lamden_buy_amount} TAU getting USDC: {bsc_sell_amount}")
