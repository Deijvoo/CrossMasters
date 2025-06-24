import pandas as pd
import random
import time
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

# --------------------------------------------------------------------------------
# PART 1: SIMULATION OF EXTERNAL SYSTEMS (API, DATABASES)
# In a real-world scenario, these would be network requests to other services.
# --------------------------------------------------------------------------------

MOCK_STOCK = {
    # product: (stock_count, weight_kg)
    'JBL Charge 4': (10, 0.96),
    'Bose QuietComfort Earbuds': (5, 0.08),
    'Sony WH-1000XM4': (0, 0.25),  # Example of an out-of-stock product
    'LG OLED55CX': (3, 23.0),
    'Samsung QN55Q80T': (4, 24.1),
    'LG 75NANO81': (1, 35.4),
    'Apple iPhone 12 Pro': (8, 0.18),
    'Samsung Galaxy S21 Ultra': (2, 0.22),
    'Xiaomi Poco X3 Pro': (15, 0.21),
    'Apple iPad Air': (6, 0.45),
    'Samsung Galaxy Tab S7+': (0, 0.57), # Another example of an out-of-stock product
    'Lenovo Tab P11 Pro': (7, 0.49),
}

def check_stock_availability(products_in_order):
    """Simulates a query to the inventory system (via API)."""
    logging.info("  -> Ověřuji dostupnost zboží na skladě...")
    total_weight = 0
    for product, required_quantity in products_in_order.items():
        stock_info = MOCK_STOCK.get(product)
        # Data validation: check if product exists in our stock system
        if stock_info is None:
            logging.error(f"  -! VALIDATION ERROR: Produkt '{product}' nenalezen v MOCK_STOCK.")
            return False, 0
            
        if stock_info[0] < required_quantity:
            available_quantity = stock_info[0]
            logging.warning(f"  -! CHYBA: Nedostatek zboží '{product}'. Požadováno: {required_quantity}, Skladem: {available_quantity}")
            return False, 0
        total_weight += stock_info[1] * required_quantity
    logging.info("  -- Zboží je dostupné.")
    return True, total_weight

def assign_shipping(order_id, total_weight):
    """Simulates selecting a carrier and assigning shipping costs based on weight."""
    logging.info(f"  -> Přiřazuji dopravu pro objednávku {order_id} (hmotnost: {total_weight:.2f} kg)...")
    if total_weight > 50:
        carrier = "PPL 'Nadměrná zásilka'"
        cost = 500
    elif total_weight > 20:
        carrier = "DPD"
        cost = 180
    else:
        carrier = "Zásilkovna"
        cost = 89
    logging.info(f"  -- Dopravce: {carrier}, Cena: {cost} Kč.")
    return carrier, cost

def arrange_insurance(order_id, total_value):
    """Simulates arranging insurance via an external insurance company's API."""
    logging.info(f"  -> Sjednávám pojištění pro objednávku {order_id} (hodnota: {total_value:,.0f} Kč)...")
    time.sleep(1) # Simulate network latency
    # Simulate a random failure of the insurance API (e.g., in 10% of cases)
    if random.random() < 0.1:
        logging.error("  -! CHYBA: API pojišťovny vrátilo chybu. Nelze pojistit.")
        return False
    logging.info("  -- Pojištění úspěšně sjednáno.")
    return True

# --------------------------------------------------------------------------------
# PART 2: MAIN LOGIC OF THE AUTOMATION SCRIPT
# --------------------------------------------------------------------------------

def process_orders(orders_df, transactions_df):
    """
    Main function that processes all new orders with the 'pending approval' status.
    """
    # Filter only the orders that need processing
    new_orders_to_process = orders_df[orders_df['status'] == 'čeká na schválení']

    if new_orders_to_process.empty:
        logging.info("Žádné nové objednávky ke zpracování.")
        return orders_df

    logging.info(f"Nalezeno {len(new_orders_to_process)} nových objednávek ke zpracování.")

    # Process each order individually
    for order_id, order_details in new_orders_to_process.iterrows():
        logging.info(f"--- Zpracovávám objednávku č. {order_id} ---")

        # Get all products in the given order
        products_in_order = {
            row['Product name']: row['Quantity']
            for _, row in transactions_df[transactions_df['Transaction ID'] == order_id].iterrows()
        }

        # STEP 1: Check stock availability and calculate total weight
        is_stock_ok, total_weight = check_stock_availability(products_in_order)
        if not is_stock_ok:
            orders_df.loc[order_id, 'status'] = 'čeká na naskladnění'
            orders_df.loc[order_id, 'notes'] = 'Jeden nebo více produktů není skladem.'
            logging.info(f"--- Objednávka č. {order_id} přesunuta do stavu 'čeká na naskladnění' ---")
            continue

        # STEP 2: Assign shipping based on weight
        carrier, shipping_cost = assign_shipping(order_id, total_weight)
        orders_df.loc[order_id, 'shipping_carrier'] = carrier
        orders_df.loc[order_id, 'shipping_cost'] = shipping_cost

        # STEP 3: Check value limit and arrange insurance
        total_value = order_details['total_value']
        insurance_needed = total_value > 100000

        if insurance_needed:
            is_insurance_ok = arrange_insurance(order_id, total_value)
            if not is_insurance_ok:
                orders_df.loc[order_id, 'status'] = 'vyžaduje manuální kontrolu'
                orders_df.loc[order_id, 'notes'] = 'Nepodařilo se sjednat pojištění pro zásilku.'
                logging.info(f"--- Objednávka č. {order_id} přesunuta do stavu 'vyžaduje manuální kontrolu' ---")
                continue
        
        # STEP 4: All checks passed, the order is approved
        orders_df.loc[order_id, 'status'] = 'schváleno - k expedici'
        orders_df.loc[order_id, 'notes'] = 'Objednávka byla automaticky schválena.'
        logging.info(f"--- Objednávka č. {order_id} SCHVÁLENA ---")

    return orders_df

if __name__ == '__main__':
    # --- SIMULATION SETUP ---
    # Load source data
    try:
        products_df = pd.read_csv('../data/in/Products.csv')
        transactions_df_raw = pd.read_csv('../data/in/Transactions.csv')
    except FileNotFoundError as e:
        logging.error(f"CHYBA: Vstupní soubor nebyl nalezen. Ujistěte se, že soubory jsou v 'data/in'. Detail: {e}")
        exit()
        
    transactions_df_raw.rename(columns={'Product name ': 'Product name'}, inplace=True)
    
    # +++ Data Validation: Check for products in transactions that are not in the product catalog +++
    products_in_catalog = set(products_df['Product name'])
    products_in_transactions = set(transactions_df_raw['Product name'])
    missing_products = products_in_transactions - products_in_catalog
    if missing_products:
        logging.warning(f"Následující produkty z transakcí nebyly nalezeny v katalogu produktů: {missing_products}")
        # Optional: filter out transactions with missing products
        # transactions_df_raw = transactions_df_raw[~transactions_df_raw['Product name'].isin(missing_products)]

    # Join data to get prices and categories
    full_transactions_df = pd.merge(transactions_df_raw, products_df, on='Product name', how='left')
    full_transactions_df['Turnover'] = full_transactions_df['Quantity'] * full_transactions_df['Price']

    # Create a "mock" orders table (in a real scenario, this would be a DB table)
    orders_table = full_transactions_df.groupby('Transaction ID').agg(
        total_value=('Turnover', 'sum')
    )
    
    # Set every 4th order as a high-value one to test the insurance for the simulation
    order_ids = orders_table.index.to_list()
    for i, order_id in enumerate(order_ids):
        if i > 0 and i % 4 == 0:
            orders_table.loc[order_id, 'total_value'] *= 2.5
    
    # Set initial statuses for all orders
    orders_table['status'] = 'čeká na schválení'  # type: ignore
    orders_table['notes'] = ''  # type: ignore
    orders_table['shipping_carrier'] = None  # type: ignore
    orders_table['shipping_cost'] = 0  # type: ignore

    logging.info("--- Počáteční stav tabulky objednávek ---")
    logging.info(f"\n{orders_table.head()}")
    
    # --- RUN AUTOMATION ---
    final_state_df = process_orders(orders_table.copy(), full_transactions_df) # Use copy to avoid SettingWithCopyWarning
    
    logging.info("--- Finální stav tabulky objednávek po zpracování ---")
    logging.info(f"\n{final_state_df}")

    # +++ Export to CSV +++
    try:
        output_path = "../data/out/output.csv"
        final_state_df.to_csv(output_path, encoding="utf-8")
        logging.info(f"Výsledky byly úspěšně uloženy do souboru {output_path}")
    except Exception as e:
        logging.error(f"Nepodařilo se uložit výsledky do CSV: {e}")
    
    logging.info("Skript na automatizaci dokončen.") 