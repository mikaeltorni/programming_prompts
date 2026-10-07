# debug-stock

Maintain process-local stock initially bolt=8 and nut=5. show ITEM returns ITEM=COUNT. reserve ITEM QUANTITY requires a positive integer quantity no greater than available stock, subtracts it and returns reserved=QUANTITY; ITEM=REMAINING. Empty/unknown commands, missing/extra arguments, malformed numeric tokens, unknown items, zero/negative and insufficient quantities raise ValueError without changing either item's stock. Public entrypoint: run_stock(command: str) -> str in stock.py.
