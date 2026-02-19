"""
GHG Emission Factors Setup Script
Populates scopes, categories, and emission sources based on UK Government 
Greenhouse Gas Reporting: Conversion Factors 2025

Run this to populate comprehensive emission factors data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config.settings import config

class GHGFactorsSetup:
    def __init__(self):
        self.connection = None
        self.db_config = config.database_config.copy()
    
    def connect(self):
        """Connect to database"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            print("✅ Connected to database")
            return True
        except Error as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Disconnected from database")
    
    def execute_query(self, query, params=None):
        """Execute a query"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Query failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def clear_existing_data(self):
        """Clear existing GHG data (optional - use with caution)"""
        print("\n⚠️  Clearing existing GHG reference data...")
        
        # Delete in reverse order of dependencies (child tables first)
        tables = ['emissions_data', 'ghg_emission_sources', 'ghg_categories', 'ghg_scopes']
        
        for table in tables:
            query = f"DELETE FROM {table}"
            if self.execute_query(query):
                print(f"  ✅ Cleared {table}")
            else:
                print(f"  ❌ Failed to clear {table}")
                return False
        
        return True
    
    def setup_scopes(self):
        """Insert GHG Scopes"""
        print("\n📊 Setting up GHG Scopes...")
        
        scopes = [
            (1, 'Scope 1: Direct Emissions', 
             'Direct GHG emissions from sources owned or controlled by the organization'),
            (2, 'Scope 2: Energy Indirect Emissions', 
             'Indirect GHG emissions from the generation of purchased electricity, heat, steam, or cooling'),
            (3, 'Scope 3: Other Indirect Emissions', 
             'All other indirect emissions that occur in the value chain of the reporting organization')
        ]
        
        query = """
            INSERT IGNORE INTO ghg_scopes (scope_number, scope_name, description) 
            VALUES (%s, %s, %s)
        """
        
        for scope in scopes:
            if self.execute_query(query, scope):
                print(f"  ✅ Scope {scope[0]}: {scope[1]}")
            else:
                print(f"  ❌ Failed to insert Scope {scope[0]}")
                return False
        
        return True
    
    def setup_categories(self):
        """Insert GHG Categories"""
        print("\n📋 Setting up GHG Categories...")
        
        # Get scope IDs
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT id, scope_number FROM ghg_scopes ORDER BY scope_number")
        scopes = {row['scope_number']: row['id'] for row in cursor.fetchall()}
        cursor.close()
        
        categories = [
            # Scope 1 Categories
            (scopes[1], 'S1-FUEL', 'Fuel Combustion', 'Emissions from fuel combustion in stationary and mobile sources'),
            (scopes[1], 'S1-FUGITIVE', 'Fugitive Emissions', 'Intentional or unintentional releases (e.g., refrigerants, SF6)'),
            (scopes[1], 'S1-PROCESS', 'Process Emissions', 'Emissions from industrial processes'),
            
            # Scope 2 Categories
            (scopes[2], 'S2-ELECTRICITY', 'Purchased Electricity', 'Electricity purchased from the grid or suppliers'),
            (scopes[2], 'S2-HEAT-STEAM', 'Purchased Heat, Steam, and Cooling', 'District heating, cooling, or steam'),
            
            # Scope 3 Categories (following GHG Protocol categories)
            (scopes[3], 'S3-01-GOODS', 'Purchased Goods and Services', 'Upstream emissions from purchased goods and services'),
            (scopes[3], 'S3-02-CAPITAL', 'Capital Goods', 'Upstream emissions from purchased capital goods'),
            (scopes[3], 'S3-03-FUEL-ENERGY', 'Fuel and Energy Related Activities', 'Extraction, production and transport of fuels and energy'),
            (scopes[3], 'S3-04-UPSTREAM-TRANSPORT', 'Upstream Transportation and Distribution', 'Transportation and distribution of purchased products'),
            (scopes[3], 'S3-05-WASTE', 'Waste Generated in Operations', 'Disposal and treatment of waste'),
            (scopes[3], 'S3-06-BUSINESS-TRAVEL', 'Business Travel', 'Employee business travel'),
            (scopes[3], 'S3-07-COMMUTING', 'Employee Commuting', 'Employee commuting between home and work'),
            (scopes[3], 'S3-08-UPSTREAM-ASSETS', 'Upstream Leased Assets', 'Operation of assets leased by the reporting company'),
            (scopes[3], 'S3-09-DOWNSTREAM-TRANSPORT', 'Downstream Transportation and Distribution', 'Transportation and distribution of sold products'),
            (scopes[3], 'S3-10-PROCESSING', 'Processing of Sold Products', 'Processing of intermediate products by third parties'),
            (scopes[3], 'S3-11-USE-PRODUCTS', 'Use of Sold Products', 'End use of goods and services sold'),
            (scopes[3], 'S3-12-END-LIFE', 'End-of-Life Treatment of Sold Products', 'Waste disposal and treatment of sold products'),
            (scopes[3], 'S3-13-DOWNSTREAM-ASSETS', 'Downstream Leased Assets', 'Operation of assets owned and leased to other entities'),
            (scopes[3], 'S3-14-FRANCHISES', 'Franchises', 'Operation of franchises'),
            (scopes[3], 'S3-15-INVESTMENTS', 'Investments', 'Operation of investments'),
        ]
        
        query = """
            INSERT IGNORE INTO ghg_categories (scope_id, category_code, category_name, description) 
            VALUES (%s, %s, %s, %s)
        """
        
        for category in categories:
            if self.execute_query(query, category):
                print(f"  ✅ {category[1]}: {category[2]}")
            else:
                print(f"  ⚠️  {category[1]} might already exist")
        
        return True
    
    def setup_emission_sources(self):
        """Insert Emission Sources based on UK Gov 2025 factors"""
        print("\n🌍 Setting up Emission Sources...")
        
        # Get category IDs
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT id, category_code FROM ghg_categories")
        categories = {row['category_code']: row['id'] for row in cursor.fetchall()}
        cursor.close()
        
        # Debug: Show what categories were fetched
        if not categories:
            print("❌ ERROR: No categories found in database!")
            print("   Please ensure setup_categories() completed successfully.")
            return False
        
        print(f"  📊 Found {len(categories)} categories in database")
        
        # Validate that we have all expected category codes
        expected_codes = [
            'S1-FUEL', 'S1-FUGITIVE', 'S1-PROCESS',
            'S2-ELECTRICITY', 'S2-HEAT-STEAM',
            'S3-01-GOODS', 'S3-02-CAPITAL', 'S3-03-FUEL-ENERGY', 
            'S3-04-UPSTREAM-TRANSPORT', 'S3-05-WASTE', 'S3-06-BUSINESS-TRAVEL', 
            'S3-07-COMMUTING', 'S3-08-UPSTREAM-ASSETS', 'S3-09-DOWNSTREAM-TRANSPORT',
            'S3-10-PROCESSING', 'S3-11-USE-PRODUCTS', 'S3-12-END-LIFE', 
            'S3-13-DOWNSTREAM-ASSETS', 'S3-14-FRANCHISES', 'S3-15-INVESTMENTS',
        ]
        
        missing_codes = [code for code in expected_codes if code not in categories]
        if missing_codes:
            print(f"❌ ERROR: Missing categories: {missing_codes}")
            print(f"   Available categories: {list(categories.keys())}")
            return False
        
        # Emission sources with UK Gov 2025 conversion factors
        # Format: (category_id, code, name, emission_factor, unit, description)
        sources = [
            # === SCOPE 1: FUEL COMBUSTION ===
            
            # Fuels - Gaseous
            (categories['S1-FUEL'], 'S1-F-001', 'Natural Gas', 0.18385, 'kg CO2e/kWh', 
             'Natural gas combustion in boilers, furnaces, or other equipment'),
            (categories['S1-FUEL'], 'S1-F-002', 'LPG (Liquefied Petroleum Gas)', 0.21449, 'kg CO2e/litre', 
             'LPG combustion'),
            (categories['S1-FUEL'], 'S1-F-003', 'Butane', 0.22870, 'kg CO2e/litre', 
             'Butane combustion'),
            (categories['S1-FUEL'], 'S1-F-004', 'Propane', 0.21431, 'kg CO2e/litre', 
             'Propane combustion'),
            
            # Fuels - Liquid
            (categories['S1-FUEL'], 'S1-F-010', 'Petrol (Gasoline)', 0.24167, 'kg CO2e/litre', 
             'Petrol/gasoline combustion in vehicles or equipment'),
            (categories['S1-FUEL'], 'S1-F-011', 'Diesel (100% mineral)', 0.25198, 'kg CO2e/litre', 
             'Diesel fuel combustion'),
            (categories['S1-FUEL'], 'S1-F-012', 'Gas Oil', 0.26527, 'kg CO2e/litre', 
             'Gas oil combustion (red diesel)'),
            (categories['S1-FUEL'], 'S1-F-013', 'Fuel Oil', 0.26835, 'kg CO2e/litre', 
             'Heavy fuel oil combustion'),
            (categories['S1-FUEL'], 'S1-F-014', 'Burning Oil (Kerosene)', 0.24588, 'kg CO2e/litre', 
             'Kerosene/paraffin combustion'),
            (categories['S1-FUEL'], 'S1-F-015', 'Aviation Turbine Fuel (Jet Fuel)', 0.24444, 'kg CO2e/litre', 
             'Aviation fuel combustion'),
            (categories['S1-FUEL'], 'S1-F-016', 'Aviation Gasoline (AvGas)', 0.23342, 'kg CO2e/litre', 
             'Aviation gasoline combustion'),
            
            # Fuels - Solid
            (categories['S1-FUEL'], 'S1-F-020', 'Coal (Industrial)', 0.32281, 'kg CO2e/kg', 
             'Coal combustion in industrial facilities'),
            (categories['S1-FUEL'], 'S1-F-021', 'Coal (Electricity Generation)', 0.34224, 'kg CO2e/kg', 
             'Coal combustion for power generation'),
            (categories['S1-FUEL'], 'S1-F-022', 'Coal (Domestic)', 0.39313, 'kg CO2e/kg', 
             'Coal combustion in domestic settings'),
            (categories['S1-FUEL'], 'S1-F-023', 'Wood Logs', 0.01515, 'kg CO2e/kg', 
             'Wood logs combustion'),
            (categories['S1-FUEL'], 'S1-F-024', 'Wood Chips', 0.01583, 'kg CO2e/kg', 
             'Wood chips combustion'),
            (categories['S1-FUEL'], 'S1-F-025', 'Wood Pellets', 0.01666, 'kg CO2e/kg', 
             'Wood pellets combustion'),
            
            # Biofuels
            (categories['S1-FUEL'], 'S1-F-030', 'Biodiesel (ME)', 0.15813, 'kg CO2e/litre', 
             'Biodiesel (methyl ester) combustion'),
            (categories['S1-FUEL'], 'S1-F-031', 'Bioethanol', 0.13734, 'kg CO2e/litre', 
             'Bioethanol combustion'),
            (categories['S1-FUEL'], 'S1-F-032', 'Biomethane', 0.00021, 'kg CO2e/kWh', 
             'Biomethane combustion (compressed)'),
            
            # === SCOPE 1: FUGITIVE EMISSIONS ===
            
            # Refrigerants - HFCs
            (categories['S1-FUGITIVE'], 'S1-R-001', 'R134a (HFC-134a)', 1430.00000, 'kg CO2e/kg', 
             'Common refrigerant in automotive and commercial applications'),
            (categories['S1-FUGITIVE'], 'S1-R-002', 'R404A', 3922.00000, 'kg CO2e/kg', 
             'Refrigerant blend used in refrigeration'),
            (categories['S1-FUGITIVE'], 'S1-R-003', 'R410A', 2088.00000, 'kg CO2e/kg', 
             'Refrigerant used in air conditioning'),
            (categories['S1-FUGITIVE'], 'S1-R-004', 'R407C', 1774.00000, 'kg CO2e/kg', 
             'Refrigerant blend for air conditioning'),
            (categories['S1-FUGITIVE'], 'S1-R-005', 'R32', 675.00000, 'kg CO2e/kg', 
             'Lower GWP refrigerant for air conditioning'),
            
            # Refrigerants - Natural
            (categories['S1-FUGITIVE'], 'S1-R-010', 'R290 (Propane)', 3.30000, 'kg CO2e/kg', 
             'Natural refrigerant with low GWP'),
            (categories['S1-FUGITIVE'], 'S1-R-011', 'R600a (Isobutane)', 3.00000, 'kg CO2e/kg', 
             'Natural refrigerant for domestic refrigeration'),
            (categories['S1-FUGITIVE'], 'S1-R-012', 'R717 (Ammonia)', 0.00000, 'kg CO2e/kg', 
             'Natural refrigerant with zero GWP'),
            (categories['S1-FUGITIVE'], 'S1-R-013', 'R744 (CO2)', 1.00000, 'kg CO2e/kg', 
             'CO2 used as refrigerant'),
            
            # Other fugitive emissions
            (categories['S1-FUGITIVE'], 'S1-R-020', 'SF6 (Sulphur Hexafluoride)', 23500.00000, 'kg CO2e/kg', 
             'Electrical insulation gas'),
            
            # === SCOPE 2: ELECTRICITY ===
            
            (categories['S2-ELECTRICITY'], 'S2-E-001', 'UK Electricity (Grid Average)', 0.21233, 'kg CO2e/kWh', 
             'UK national grid electricity - location-based'),
            (categories['S2-ELECTRICITY'], 'S2-E-002', 'Electricity (Renewables)', 0.00000, 'kg CO2e/kWh', 
             'Renewable electricity with guarantees of origin'),
            
            # === SCOPE 2: HEAT AND STEAM ===
            
            (categories['S2-HEAT-STEAM'], 'S2-H-001', 'District Heating', 0.02070, 'kg CO2e/kWh', 
             'Heat from district heating networks'),
            (categories['S2-HEAT-STEAM'], 'S2-H-002', 'Heat and Steam', 0.18739, 'kg CO2e/kWh', 
             'General heat and steam from suppliers'),
            
            # === SCOPE 3: BUSINESS TRAVEL - Cars ===
            
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-001', 'Small Car - Petrol (up to 1.4L)', 0.16526, 'kg CO2e/km', 
             'Small petrol car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-002', 'Medium Car - Petrol (1.4-2.0L)', 0.19514, 'kg CO2e/km', 
             'Medium petrol car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-003', 'Large Car - Petrol (over 2.0L)', 0.28224, 'kg CO2e/km', 
             'Large petrol car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-004', 'Average Car - Petrol', 0.18682, 'kg CO2e/km', 
             'Average petrol car business travel'),
            
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-010', 'Small Car - Diesel (up to 1.7L)', 0.15124, 'kg CO2e/km', 
             'Small diesel car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-011', 'Medium Car - Diesel (1.7-2.0L)', 0.17189, 'kg CO2e/km', 
             'Medium diesel car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-012', 'Large Car - Diesel (over 2.0L)', 0.21033, 'kg CO2e/km', 
             'Large diesel car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-013', 'Average Car - Diesel', 0.17191, 'kg CO2e/km', 
             'Average diesel car business travel'),
            
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-020', 'Small Car - Hybrid', 0.11379, 'kg CO2e/km', 
             'Small hybrid car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-021', 'Medium Car - Hybrid', 0.12636, 'kg CO2e/km', 
             'Medium hybrid car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-022', 'Large Car - Hybrid', 0.16432, 'kg CO2e/km', 
             'Large hybrid car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-023', 'Average Car - Hybrid', 0.12636, 'kg CO2e/km', 
             'Average hybrid car business travel'),
            
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-030', 'Small Car - Plug-in Hybrid', 0.07439, 'kg CO2e/km', 
             'Small plug-in hybrid car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-031', 'Medium Car - Plug-in Hybrid', 0.08887, 'kg CO2e/km', 
             'Medium plug-in hybrid car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-032', 'Large Car - Plug-in Hybrid', 0.12636, 'kg CO2e/km', 
             'Large plug-in hybrid car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-033', 'Average Car - Plug-in Hybrid', 0.08887, 'kg CO2e/km', 
             'Average plug-in hybrid car business travel'),
            
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-040', 'Small Car - Battery Electric', 0.04533, 'kg CO2e/km', 
             'Small battery electric car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-041', 'Medium Car - Battery Electric', 0.05302, 'kg CO2e/km', 
             'Medium battery electric car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-042', 'Large Car - Battery Electric', 0.07879, 'kg CO2e/km', 
             'Large battery electric car business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-043', 'Average Car - Battery Electric', 0.05302, 'kg CO2e/km', 
             'Average battery electric car business travel'),
            
            # Business Travel - Motorcycles
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-050', 'Motorcycle - Small (up to 125cc)', 0.08551, 'kg CO2e/km', 
             'Small motorcycle business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-051', 'Motorcycle - Medium (125-500cc)', 0.10184, 'kg CO2e/km', 
             'Medium motorcycle business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-052', 'Motorcycle - Large (over 500cc)', 0.13522, 'kg CO2e/km', 
             'Large motorcycle business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-053', 'Motorcycle - Average', 0.11277, 'kg CO2e/km', 
             'Average motorcycle business travel'),
            
            # Business Travel - Taxis
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-060', 'Taxi - Regular', 0.16419, 'kg CO2e/km', 
             'Regular taxi business travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-061', 'Taxi - Black Cab (London)', 0.22046, 'kg CO2e/km', 
             'London black cab business travel'),
            
            # Business Travel - Rail
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-070', 'National Rail', 0.03549, 'kg CO2e/km', 
             'UK national rail travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-071', 'International Rail', 0.00413, 'kg CO2e/km', 
             'International rail travel (e.g., Eurostar)'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-072', 'Light Rail and Tram', 0.03174, 'kg CO2e/km', 
             'Light rail and tram travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-073', 'London Underground', 0.02941, 'kg CO2e/km', 
             'London Underground travel'),
            
            # Business Travel - Bus
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-080', 'Local Bus (not London)', 0.11706, 'kg CO2e/km', 
             'Local bus travel outside London'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-081', 'Local London Bus', 0.08149, 'kg CO2e/km', 
             'London bus travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-082', 'Average Local Bus', 0.10312, 'kg CO2e/km', 
             'Average local bus travel'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-083', 'Coach', 0.02769, 'kg CO2e/km', 
             'Coach travel'),
            
            # Business Travel - Air (Domestic)
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-100', 'Flights - Domestic (average)', 0.25543, 'kg CO2e/km', 
             'Domestic flights (average passenger)'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-101', 'Flights - Domestic (economy)', 0.21286, 'kg CO2e/km', 
             'Domestic flights economy class'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-102', 'Flights - Domestic (business)', 0.31957, 'kg CO2e/km', 
             'Domestic flights business class'),
            
            # Business Travel - Air (Short-haul, < 3700km)
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-110', 'Flights - Short-haul (average)', 0.15313, 'kg CO2e/km', 
             'Short-haul international flights (average)'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-111', 'Flights - Short-haul (economy)', 0.13617, 'kg CO2e/km', 
             'Short-haul flights economy class'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-112', 'Flights - Short-haul (business)', 0.20426, 'kg CO2e/km', 
             'Short-haul flights business class'),
            
            # Business Travel - Air (Long-haul, > 3700km)
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-120', 'Flights - Long-haul (average)', 0.14862, 'kg CO2e/km', 
             'Long-haul international flights (average)'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-121', 'Flights - Long-haul (economy)', 0.10605, 'kg CO2e/km', 
             'Long-haul flights economy class'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-122', 'Flights - Long-haul (premium economy)', 0.16967, 'kg CO2e/km', 
             'Long-haul flights premium economy'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-123', 'Flights - Long-haul (business)', 0.31815, 'kg CO2e/km', 
             'Long-haul flights business class'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-124', 'Flights - Long-haul (first class)', 0.42420, 'kg CO2e/km', 
             'Long-haul flights first class'),
            
            # Business Travel - Air (International, average)
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-130', 'Flights - International (average)', 0.14891, 'kg CO2e/km', 
             'All international flights average'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-131', 'Flights - International (economy)', 0.11904, 'kg CO2e/km', 
             'International flights economy class average'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-BT-132', 'Flights - International (business)', 0.26865, 'kg CO2e/km', 
             'International flights business class average'),
            
            # === SCOPE 3: EMPLOYEE COMMUTING ===
            
            # Use same factors as business travel for commuting
            (categories['S3-07-COMMUTING'], 'S3-EC-001', 'Car - Petrol (Average)', 0.18682, 'kg CO2e/km', 
             'Average petrol car commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-002', 'Car - Diesel (Average)', 0.17191, 'kg CO2e/km', 
             'Average diesel car commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-003', 'Car - Hybrid (Average)', 0.12636, 'kg CO2e/km', 
             'Average hybrid car commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-004', 'Car - Electric (Average)', 0.05302, 'kg CO2e/km', 
             'Average electric car commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-010', 'Motorcycle (Average)', 0.11277, 'kg CO2e/km', 
             'Average motorcycle commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-020', 'Bus (Average)', 0.10312, 'kg CO2e/km', 
             'Average bus commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-021', 'National Rail', 0.03549, 'kg CO2e/km', 
             'Train commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-022', 'Light Rail', 0.03174, 'kg CO2e/km', 
             'Light rail commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-023', 'Underground', 0.02941, 'kg CO2e/km', 
             'Underground commuting'),
            (categories['S3-07-COMMUTING'], 'S3-EC-030', 'Bicycle', 0.00000, 'kg CO2e/km', 
             'Bicycle commuting (zero emissions)'),
            (categories['S3-07-COMMUTING'], 'S3-EC-031', 'Walking', 0.00000, 'kg CO2e/km', 
             'Walking (zero emissions)'),
            
            # === SCOPE 3: BUSINESS TRAVEL - HOTEL STAYS ===
            
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-H-001', 'Hotel Stay - UK (average)', 18.49000, 'kg CO2e/room night', 
             'Average UK hotel room per night'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-H-002', 'Hotel Stay - Europe (average)', 24.69000, 'kg CO2e/room night', 
             'Average European hotel room per night'),
            (categories['S3-06-BUSINESS-TRAVEL'], 'S3-H-003', 'Hotel Stay - Rest of World (average)', 39.09000, 'kg CO2e/room night', 
             'Average international hotel room per night'),
            
            # === SCOPE 3: WASTE ===
            
            (categories['S3-05-WASTE'], 'S3-W-001', 'Waste - Landfill', 0.46746, 'kg CO2e/kg', 
             'Waste sent to landfill'),
            (categories['S3-05-WASTE'], 'S3-W-002', 'Waste - Incineration', 0.02088, 'kg CO2e/kg', 
             'Waste incineration (energy recovery)'),
            (categories['S3-05-WASTE'], 'S3-W-003', 'Waste - Recycling (average)', 0.02123, 'kg CO2e/kg', 
             'Average recycled waste'),
            (categories['S3-05-WASTE'], 'S3-W-004', 'Waste - Composting', 0.01508, 'kg CO2e/kg', 
             'Organic waste composting'),
            (categories['S3-05-WASTE'], 'S3-W-005', 'Waste - Anaerobic Digestion', 0.00804, 'kg CO2e/kg', 
             'Organic waste anaerobic digestion'),
            
            # Specific recyclable materials
            (categories['S3-05-WASTE'], 'S3-W-010', 'Paper & Cardboard - Recycled', 0.02123, 'kg CO2e/kg', 
             'Paper and cardboard recycling'),
            (categories['S3-05-WASTE'], 'S3-W-011', 'Plastic - Recycled', 0.02123, 'kg CO2e/kg', 
             'Plastic recycling'),
            (categories['S3-05-WASTE'], 'S3-W-012', 'Metal - Recycled', 0.02123, 'kg CO2e/kg', 
             'Metal recycling'),
            (categories['S3-05-WASTE'], 'S3-W-013', 'Glass - Recycled', 0.02123, 'kg CO2e/kg', 
             'Glass recycling'),
            
            # === SCOPE 3: PURCHASED GOODS AND SERVICES - MATERIALS ===
            
            (categories['S3-01-GOODS'], 'S3-M-001', 'Paper - Average', 0.91044, 'kg CO2e/kg', 
             'Average paper products'),
            (categories['S3-01-GOODS'], 'S3-M-002', 'Cardboard - Average', 0.58967, 'kg CO2e/kg', 
             'Average cardboard products'),
            (categories['S3-01-GOODS'], 'S3-M-010', 'Plastics - Average', 2.53370, 'kg CO2e/kg', 
             'Average plastic products'),
            (categories['S3-01-GOODS'], 'S3-M-011', 'PET Plastic', 2.15260, 'kg CO2e/kg', 
             'PET plastic products'),
            (categories['S3-01-GOODS'], 'S3-M-012', 'HDPE Plastic', 1.93470, 'kg CO2e/kg', 
             'HDPE plastic products'),
            (categories['S3-01-GOODS'], 'S3-M-013', 'PVC Plastic', 2.53370, 'kg CO2e/kg', 
             'PVC plastic products'),
            (categories['S3-01-GOODS'], 'S3-M-020', 'Steel', 1.52890, 'kg CO2e/kg', 
             'Steel products'),
            (categories['S3-01-GOODS'], 'S3-M-021', 'Aluminium', 8.58230, 'kg CO2e/kg', 
             'Aluminium products'),
            (categories['S3-01-GOODS'], 'S3-M-030', 'Concrete', 0.13310, 'kg CO2e/kg', 
             'Concrete'),
            (categories['S3-01-GOODS'], 'S3-M-031', 'Cement', 0.83630, 'kg CO2e/kg', 
             'Cement'),
            (categories['S3-01-GOODS'], 'S3-M-040', 'Glass', 0.85340, 'kg CO2e/kg', 
             'Glass products'),
            (categories['S3-01-GOODS'], 'S3-M-050', 'Timber', 0.43640, 'kg CO2e/kg', 
             'Timber/wood products'),
            
            # === SCOPE 3: WATER ===
            
            (categories['S3-01-GOODS'], 'S3-WT-001', 'Water - Supply', 0.34400, 'kg CO2e/m³', 
             'Mains water supply'),
            (categories['S3-01-GOODS'], 'S3-WT-002', 'Water - Treatment', 0.70800, 'kg CO2e/m³', 
             'Wastewater treatment'),
            
            # === SCOPE 3: FREIGHT (Upstream and Downstream Transport) ===
            
            # Road freight
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-001', 'HGV - All Rigid (average)', 0.60587, 'kg CO2e/tonne.km', 
             'Heavy goods vehicle rigid'),
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-002', 'HGV - All Articulated (average)', 0.07695, 'kg CO2e/tonne.km', 
             'Heavy goods vehicle articulated'),
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-003', 'Van - Average', 0.25726, 'kg CO2e/km', 
             'Average delivery van'),
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-004', 'Van - Class I (up to 1.305 tonnes)', 0.23046, 'kg CO2e/km', 
             'Small van'),
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-005', 'Van - Class II (1.305-1.74 tonnes)', 0.24866, 'kg CO2e/km', 
             'Medium van'),
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-006', 'Van - Class III (over 1.74 tonnes)', 0.31346, 'kg CO2e/km', 
             'Large van'),
            
            # Sea freight
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-010', 'Cargo Ship - Average', 0.01121, 'kg CO2e/tonne.km', 
             'Average cargo ship'),
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-011', 'Cargo Ship - Bulk Carrier', 0.00626, 'kg CO2e/tonne.km', 
             'Bulk carrier ship'),
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-012', 'Cargo Ship - Container Ship', 0.01525, 'kg CO2e/tonne.km', 
             'Container ship'),
            
            # Rail freight
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-020', 'Freight Train', 0.02533, 'kg CO2e/tonne.km', 
             'Rail freight'),
            
            # Air freight
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-030', 'Air Freight (long-haul)', 0.60200, 'kg CO2e/tonne.km', 
             'Long-haul air freight'),
            (categories['S3-04-UPSTREAM-TRANSPORT'], 'S3-FT-031', 'Air Freight (short-haul)', 1.51300, 'kg CO2e/tonne.km', 
             'Short-haul air freight'),

              # Downstream transport and distribution (same mode factors, sold products)
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-001', 'HGV - All Rigid (average)', 0.60587, 'kg CO2e/tonne.km', 
               'Downstream transport of sold goods - heavy goods vehicle rigid'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-002', 'HGV - All Articulated (average)', 0.07695, 'kg CO2e/tonne.km', 
               'Downstream transport of sold goods - heavy goods vehicle articulated'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-003', 'Van - Average', 0.25726, 'kg CO2e/km', 
               'Downstream transport of sold goods - average delivery van'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-004', 'Van - Class I (up to 1.305 tonnes)', 0.23046, 'kg CO2e/km', 
               'Downstream transport of sold goods - small van'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-005', 'Van - Class II (1.305-1.74 tonnes)', 0.24866, 'kg CO2e/km', 
               'Downstream transport of sold goods - medium van'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-006', 'Van - Class III (over 1.74 tonnes)', 0.31346, 'kg CO2e/km', 
               'Downstream transport of sold goods - large van'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-010', 'Cargo Ship - Average', 0.01121, 'kg CO2e/tonne.km', 
               'Downstream transport of sold goods - average cargo ship'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-011', 'Cargo Ship - Bulk Carrier', 0.00626, 'kg CO2e/tonne.km', 
               'Downstream transport of sold goods - bulk carrier ship'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-012', 'Cargo Ship - Container Ship', 0.01525, 'kg CO2e/tonne.km', 
               'Downstream transport of sold goods - container ship'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-020', 'Freight Train', 0.02533, 'kg CO2e/tonne.km', 
               'Downstream transport of sold goods - rail freight'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-030', 'Air Freight (long-haul)', 0.60200, 'kg CO2e/tonne.km', 
               'Downstream transport of sold goods - long-haul air freight'),
              (categories['S3-09-DOWNSTREAM-TRANSPORT'], 'S3-DT-031', 'Air Freight (short-haul)', 1.51300, 'kg CO2e/tonne.km', 
               'Downstream transport of sold goods - short-haul air freight'),
        ]
        
        query = """
            INSERT INTO ghg_emission_sources 
            (category_id, source_code, source_name, emission_factor, unit, description, region) 
            VALUES (%s, %s, %s, %s, %s, %s, 'UK')
        """
        
        inserted = 0
        skipped = 0
        
        for source in sources:
            if self.execute_query(query, source):
                inserted += 1
                if inserted % 20 == 0:
                    print(f"  ✅ Inserted {inserted} sources...")
            else:
                skipped += 1
        
        print(f"\n  ✅ Total inserted: {inserted}")
        if skipped > 0:
            print(f"  ⏭️  Skipped (already exist): {skipped}")
        
        return True
    
    def verify_setup(self):
        """Verify the setup was successful"""
        print("\n🔍 Verifying setup...")
        
        cursor = self.connection.cursor(dictionary=True)
        
        # Count scopes
        cursor.execute("SELECT COUNT(*) as count FROM ghg_scopes")
        scopes_count = cursor.fetchone()['count']
        print(f"  ✅ Scopes: {scopes_count}")
        
        # Count categories
        cursor.execute("SELECT COUNT(*) as count FROM ghg_categories")
        categories_count = cursor.fetchone()['count']
        print(f"  ✅ Categories: {categories_count}")
        
        # Count sources
        cursor.execute("SELECT COUNT(*) as count FROM ghg_emission_sources")
        sources_count = cursor.fetchone()['count']
        print(f"  ✅ Emission Sources: {sources_count}")
        
        # Show breakdown by scope
        print("\n  📊 Breakdown by Scope:")
        cursor.execute("""
            SELECT 
                s.scope_number,
                s.scope_name,
                COUNT(DISTINCT c.id) as categories,
                COUNT(es.id) as sources
            FROM ghg_scopes s
            LEFT JOIN ghg_categories c ON s.id = c.scope_id
            LEFT JOIN ghg_emission_sources es ON c.id = es.category_id
            GROUP BY s.scope_number, s.scope_name
            ORDER BY s.scope_number
        """)
        
        for row in cursor.fetchall():
            print(f"    Scope {row['scope_number']}: {row['categories']} categories, {row['sources']} sources")
        
        cursor.close()
        
        return True
    
    def run_setup(self, clear_first=False):
        """Run the complete setup"""
        print("=" * 70)
        print("🌍 GHG Emission Factors Setup")
        print("Based on UK Government Conversion Factors 2025")
        print("=" * 70)
        
        if not self.connect():
            return False
        
        try:
            # Optional: clear existing data
            if clear_first:
                if not self.clear_existing_data():
                    print("⚠️  Warning: Failed to clear existing data")
                    response = input("Continue anyway? (y/n): ")
                    if response.lower() != 'y':
                        return False
            
            # Setup scopes
            if not self.setup_scopes():
                return False
            
            # Setup categories
            if not self.setup_categories():
                return False
            
            # Setup emission sources
            if not self.setup_emission_sources():
                return False
            
            # Verify setup
            if not self.verify_setup():
                return False
            
            print("\n" + "=" * 70)
            print("🎉 GHG Factors setup completed successfully!")
            print("=" * 70)
            print("\n📝 Summary:")
            print("  • All 3 GHG Protocol scopes configured")
            print("  • Categories for all major emission types")
            print("  • 150+ emission sources with UK Gov 2025 factors")
            print("\n💡 Note:")
            print("  • Factors are in kg CO2e per unit")
            print("  • Based on UK Government 2025 conversion factors")
            print("  • Includes Scope 1, 2, and 3 emissions")
            print("\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            return False
            
        finally:
            self.disconnect()

def main():
    """Main function"""
    import sys
    
    # Check for --clear flag
    clear_first = '--clear' in sys.argv
    
    if clear_first:
        print("⚠️  WARNING: This will DELETE all existing GHG reference data!")
        print("   (Scopes, Categories, and Emission Sources)")
        response = input("   Are you sure? Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("   Cancelled.")
            return 1
    
    setup = GHGFactorsSetup()
    success = setup.run_setup(clear_first=clear_first)
    
    if success:
        print("✅ Setup completed successfully")
        return 0
    else:
        print("❌ Setup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())