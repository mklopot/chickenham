import requests


def get_confirmations(txid, retries=3):
    current_block_height = None
    tx_block_height = None
    attempts = 0
    while not (tx_block_height and current_block_height) or attempts < retries:
        try:
            attempts += 1
            r = requests.get("http://blockchain.info/tx/{}?show_adv=false&format=json".format(txid),
                             timeout=60)
            tx_block_height = r.json()["block_height"]
        except Exception:
            continue
        try:
            current_block_height = int(requests.get("https://blockchain.info/q/getblockcount",
                                                    timeout=60).text)
        except Exception:
            continue

    if current_block_height and tx_block_height:
        return current_block_height - tx_block_height + 1
    else:
        return None
