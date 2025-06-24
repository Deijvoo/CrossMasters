import pandas as pd
import unittest
from unittest.mock import patch
import sys
import os

# Add the 'src' directory to the Python path to allow imports of our scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import order_automation # The script we are testing

class TestOrderAutomation(unittest.TestCase):

    def setUp(self):
        """Set up mock data for tests that is shared across multiple test methods."""
        # Create a sample products dataframe, mirroring the structure of Products.csv
        self.products_df = pd.DataFrame({
            'Product name': ['Product A', 'Product B', 'HighValue Product C'],
            'Category': ['Cat 1', 'Cat 1', 'Cat 2'],
            'Price': [100, 500, 150000] # Product C is a high-value item
        })
        
        # Create sample transactions, mirroring the structure of Transactions.csv
        # Order 1: Standard, should pass.
        # Order 2: Uses Product A, will be used for out-of-stock test.
        # Order 3: High value, will be used to test insurance logic.
        self.transactions_df = pd.DataFrame({
            'Transaction ID': [1, 1, 2, 3],
            'Date': ['2023-01-01'] * 4,
            'Product name': ['Product A', 'Product B', 'Product A', 'HighValue Product C'],
            'Quantity': [1, 1, 1, 1]
        })
        
        # Create the "full" transactions df by merging product details, as done in the main script
        self.full_transactions_df = pd.merge(self.transactions_df, self.products_df, on='Product name', how='left')
        self.full_transactions_df['Turnover'] = self.full_transactions_df['Quantity'] * self.full_transactions_df['Price']

    @patch('order_automation.check_stock_availability')
    @patch('order_automation.assign_shipping')
    @patch('order_automation.arrange_insurance')
    def test_successful_standard_order(self, mock_arrange_insurance, mock_assign_shipping, mock_check_stock):
        """Test a standard order that should be approved automatically."""
        # --- Arrange ---
        # Mock the external system calls to always return success
        mock_check_stock.return_value = (True, 5.0) # stock is available, total weight 5kg
        mock_assign_shipping.return_value = ('Test Carrier', 100)
        
        # Create a sample order dataframe for processing, representing a single order
        order_to_process = pd.DataFrame({
            'total_value': [600], # 1*100 (Prod A) + 1*500 (Prod B)
            'status': ['čeká na schválení'],
            'notes': [''], 'shipping_carrier': [None], 'shipping_cost': [0]
        }, index=pd.Index([1], name='Transaction ID'))

        # --- Act ---
        # Process the order
        result_df = order_automation.process_orders(order_to_process, self.full_transactions_df)
        
        # --- Assert ---
        final_status = result_df.loc[1, 'status']
        self.assertEqual(final_status, 'schváleno - k expedici')
        mock_check_stock.assert_called_once()
        mock_assign_shipping.assert_called_once()
        mock_arrange_insurance.assert_not_called() # Insurance should not be called for low-value orders

    @patch('order_automation.check_stock_availability')
    def test_out_of_stock_order(self, mock_check_stock):
        """Test an order that should be moved to 'waiting for stock' status."""
        # --- Arrange ---
        # Mock the stock check to return False (out of stock)
        mock_check_stock.return_value = (False, 0)

        # Create a sample order for processing
        order_to_process = pd.DataFrame({
            'total_value': [100], # 1*100 (Prod A)
            'status': ['čeká na schválení'],
            'notes': [''], 'shipping_carrier': [None], 'shipping_cost': [0]
        }, index=pd.Index([2], name='Transaction ID'))

        # --- Act ---
        result_df = order_automation.process_orders(order_to_process, self.full_transactions_df)

        # --- Assert ---
        final_status = result_df.loc[2, 'status']
        self.assertEqual(final_status, 'čeká na naskladnění')

    @patch('order_automation.check_stock_availability')
    @patch('order_automation.assign_shipping')
    @patch('order_automation.arrange_insurance')
    def test_high_value_order_with_insurance_failure(self, mock_arrange_insurance, mock_assign_shipping, mock_check_stock):
        """Test a high-value order where the insurance arrangement fails, requiring manual review."""
        # --- Arrange ---
        # Mock external systems: stock is OK, but insurance fails
        mock_check_stock.return_value = (True, 10.0)
        mock_assign_shipping.return_value = ('Test Carrier', 200)
        mock_arrange_insurance.return_value = False # Insurance API call fails

        # Create a high-value order for processing
        order_to_process = pd.DataFrame({
            'total_value': [150000], # From HighValue Product C
            'status': ['čeká na schválení'],
            'notes': [''], 'shipping_carrier': [None], 'shipping_cost': [0]
        }, index=pd.Index([3], name='Transaction ID'))

        # --- Act ---
        result_df = order_automation.process_orders(order_to_process, self.full_transactions_df)
        
        # --- Assert ---
        final_status = result_df.loc[3, 'status']
        self.assertEqual(final_status, 'vyžaduje manuální kontrolu')
        mock_check_stock.assert_called_once()
        mock_assign_shipping.assert_called_once()
        mock_arrange_insurance.assert_called_once() # Insurance should be called

if __name__ == '__main__':
    unittest.main() 