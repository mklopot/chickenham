def get_confirmations(txid, retries=3):
        current_block_height = None
        tx_block_height = None
        attempts = 0
        while not (confirmations and current_block_height) or attempts < retries:
            try:
                attempts += 1
                r = requests.get("http://blockchain.info/tx/{}?show_adv=false&format=json".format(txid))
                tx_block_height = r.json()["block_height"]
            except Exception:
                continue
            try:
                current_block_height = int(requests.get("https://blockchain.info/q/getblockcount").text)
            except Exception:
                continue
        if current_block_height and tx_block_height:
            retrun current_block_height - tx_block_height + 1
        else:
            retrun None
