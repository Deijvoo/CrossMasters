import pandas as pd
import sys

def load_and_prepare_data(products_path='../data/in/Products.csv', transactions_path='../data/in/Transactions.csv'):
    """
    Loads and prepares data from CSV files.
    - Loads products and transactions.
    - Renames the column with an extra space.
    - Merges the tables.
    - Converts the date column to the correct format.
    - Calculates turnover.
    Returns the prepared DataFrame.
    """
    try:
        products_df = pd.read_csv(products_path)
        transactions_df = pd.read_csv(transactions_path)
    except FileNotFoundError as e:
        print(f"Chyba: Súbor nebol nájdený. Uistite sa, že súbory sú v priečinku 'data/in'. Detaily: {e}", file=sys.stderr)
        sys.exit(1)

    # Fix column name
    transactions_df.rename(columns={'Product name ': 'Product name'}, inplace=True)

    # Merge tables
    df = pd.merge(transactions_df, products_df, on='Product name', how='left')

    # Convert date
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

    # Calculate turnover
    df['Turnover'] = df['Quantity'] * df['Price']
    
    return df

def analyze_turnover_by_category(df):
    """Analyzes and prints turnover by category."""
    print("1. Na jaké kategorii produktů máme největší obrat? A zajímalo by mě i jestli se to v jednotlivých měsících mění.\n")
    
    # Total turnover
    category_turnover = df.groupby('Category')['Turnover'].sum().sort_values(ascending=False)
    print("Celkový obrat podle kategorií:")
    print(category_turnover.to_string(float_format='{:,.0f} Kč'.format))
    print(f"\n-> Největší obrat je v kategorii: {category_turnover.index[0]}\n")

    # Monthly turnover
    df['Month'] = df['Date'].dt.to_period('M')
    monthly_category_turnover = df.groupby(['Month', 'Category'])['Turnover'].sum().unstack(fill_value=0)
    print("Obrat podle kategorií v jednotlivých měsících:")
    print(monthly_category_turnover.to_string(float_format='{:,.0f} Kč'.format))
    
    print("\nNejprodávanější kategorie v jednotlivých měsících:")
    best_monthly_category = monthly_category_turnover.idxmax(axis=1)
    for month, best_category in best_monthly_category.items():
        print(f"-> {month}: {best_category}")
        
    print("\nZávěr k otázce 1:")
    print("Postup: Pro výpočet celkového obratu jsem sečetl tržby pro každou kategorii produktů. Pro měsíční analýzu jsem přidal sloupec s měsícem a následně opět sečetl tržby pro jednotlivé kategorie v každém měsíci.")
    print("Celkově má největší obrat kategorie Televize. Tato kategorie je dominantní ve všech sledovaných měsících.")

def analyze_orders_by_weekday(df):
    """Analyzes and prints the number of orders by weekday."""
    print("\n\n2. Který den v týdnu je nejsilnější na počet objednávek?\n")
    
    df['Day of Week'] = df['Date'].dt.day_name()
    orders_per_day = df.drop_duplicates(subset='Transaction ID').groupby('Day of Week')['Transaction ID'].count()
    
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    czech_days = {"Monday": "Pondělí", "Tuesday": "Úterý", "Wednesday": "Středa", "Thursday": "Čtvrtek", "Friday": "Pátek", "Saturday": "Sobota", "Sunday": "Neděle"}
    
    orders_per_day = orders_per_day.reindex(days_order).fillna(0).astype(int)
    orders_per_day.index = orders_per_day.index.map(czech_days)
    
    print("Počet objednávek podle dne v týdnu:")
    print(orders_per_day.to_string())
    print("\n-> Nejsilnější dny v týdnu na počet objednávek jsou Pondělí a Sobota.")
    
    print("\nZávěr k otázce 2:")
    print("Postup: Ze sloupce s datem jsem extrahoval název dne v týdnu. Následně jsem spočítal unikátní počet objednávek (Transaction ID) pro každý den.")
    print("Nejvíce objednávek bylo zaznamenáno v pondělí a v sobotu.")

def analyze_cosold_with_tv(df):
    """Analyzes and prints what is most often bought with a TV."""
    print("\n\n3. Která kategorie se prodává nejčastěji spolu s produkty z kategorie Televize?\n")
    
    tv_transactions = df[df['Category'] == 'Televize']['Transaction ID'].unique()
    co_sold_products = df[df['Transaction ID'].isin(tv_transactions)]
    co_sold_categories = co_sold_products[co_sold_products['Category'] != 'Televize']['Category'].value_counts()
    
    print("Kategorie prodávané spolu s kategorií Televize:")
    print(co_sold_categories.to_string())
    
    if not co_sold_categories.empty:
        most_common_category = co_sold_categories.index[0]
        print(f"\n-> Nejčastěji spolu s Televizí se prodává kategorie: {most_common_category}")
    else:
        print("\nS televizemi se neprodávají žádné další produkty.")
        
    print("\nZávěr k otázce 3:")
    print("Postup: Nejprve jsem identifikoval všechny transakce obsahující produkt z kategorie 'Televize'. Poté jsem v těchto transakcích vyhledal všechny ostatní zakoupené produkty, spočítal jejich kategorie a určil tu nejčastější.")

def analyze_marketing_impact(df, change_date_str='2022-03-18'):
    """Analyzes and prints the impact of the marketing budget change."""
    print(f"\n\n4. Od {pd.to_datetime(change_date_str).date()} byl navýšen budget na online marketing. Dovedeš mi říct, jestli to vedlo k nějaké změně v prodeji?\n")
    
    change_date = pd.to_datetime(change_date_str)
    before_df = df[df['Date'] < change_date]
    after_df = df[df['Date'] >= change_date]

    turnover_before = before_df['Turnover'].sum()
    turnover_after = after_df['Turnover'].sum()
    orders_before = before_df['Transaction ID'].nunique()
    orders_after = after_df['Transaction ID'].nunique()

    days_before = (change_date - df['Date'].min()).days if not before_df.empty else 0
    days_after = (df['Date'].max() - change_date).days if not after_df.empty else 0

    avg_daily_turnover_before = turnover_before / days_before if days_before > 0 else 0
    avg_daily_turnover_after = turnover_after / days_after if days_after > 0 else 0
    avg_daily_orders_before = orders_before / days_before if days_before > 0 else 0
    avg_daily_orders_after = orders_after / days_after if days_after > 0 else 0
    
    print(f"Analýza období před a po {change_date.date()}:")
    print(f"                                       Před              Po")
    print(f"--------------------------------------------------------------")
    print(f"Počet dní v období:                      {days_before:<12}    {days_after:<12}")
    print(f"Celkový obrat:                 {turnover_before:12,.0f} Kč {turnover_after:12,.0f} Kč")
    print(f"Celkový počet objednávek:                {orders_before:<12}    {orders_after:<12}")
    print(f"Průměrný denní obrat:          {avg_daily_turnover_before:12,.0f} Kč {avg_daily_turnover_after:12,.0f} Kč")
    print(f"Průměrný denní počet objednávek:       {avg_daily_orders_before:<12.2f}    {avg_daily_orders_after:<12.2f}")

    print("\nZávěr k otázce 4:")
    print("Postup: Provedl jsem srovnání klíčových metrik (obrat, počet objednávek) v obdobích před a po 18. 3. 2022. Aby bylo srovnání relevantní, zohlednil jsem různou délku těchto období a vypočítal průměrné denní hodnoty.")
    print(f"Po navýšení marketingového budgetu došlo k poklesu jak v průměrném denním obratu, tak v průměrném denním počtu objednávek. Průměrný denní obrat klesl z přibližně {avg_daily_turnover_before:,.0f} Kč na {avg_daily_turnover_after:,.0f} Kč a průměrný počet objednávek denně klesl z {avg_daily_orders_before:.2f} na {avg_daily_orders_after:.2f}.")
    print("Z těchto dat se zdá, že navýšení rozpočtu na marketing nemělo bezprostřední pozitivní vliv na prodeje, ba naopak. Dopad marketingových kampaní se však může projevit s delším časovým odstupem a pro přesnější vyhodnocení by bylo potřeba analyzovat delší časové období.")

def main():
    """Main function of the script that controls data loading and analysis."""
    print("--- Analýza prodejních dat ---")
    print("Následuje zodpovězení otázek od manažera e-shopu. U každé otázky je popsán postup a uveden závěr.\n")
    
    # Load and prepare data
    df = load_and_prepare_data()
    
    # Individual analyses
    analyze_turnover_by_category(df)
    analyze_orders_by_weekday(df)
    analyze_cosold_with_tv(df)
    analyze_marketing_impact(df)

if __name__ == '__main__':
    main()


