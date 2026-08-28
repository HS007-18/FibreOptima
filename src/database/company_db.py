"""Company Operations Database - Simulated Factory Database."""

import sqlite3
import json
import os
import pandas as pd
from typing import Dict, Any, Optional

class CompanyDatabase:
    """Lightweight SQLite wrapper for the company's structured machine data."""
    
    def __init__(self, data_dir: str = "data/production"):
        self.data_dir = data_dir
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._initialize_db()
        
    def _initialize_db(self):
        """Load JSON/CSV data into SQLite for demo purposes."""
        cursor = self.conn.cursor()
        
        # 1. Machine Catalog
        cursor.execute('''
            CREATE TABLE machine_catalog (
                machine_id TEXT PRIMARY KEY,
                machine_type TEXT,
                rated_capacity REAL,
                rated_speed REAL,
                installation_date TEXT,
                status TEXT
            )
        ''')
        
        catalog_path = os.path.join(self.data_dir, "machine_catalog.json")
        if os.path.exists(catalog_path):
            with open(catalog_path, "r") as f:
                catalog = json.load(f)
                for c in catalog:
                    cursor.execute('''
                        INSERT INTO machine_catalog 
                        (machine_id, machine_type, rated_capacity, rated_speed, installation_date, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        c['machine_id'], c['machine_type'], c['rated_capacity'], 
                        c['rated_speed'], c['installation_date'], c['status']
                    ))
        
        # 2. Maintenance Log
        cursor.execute('''
            CREATE TABLE maintenance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT,
                maintenance_date TEXT,
                days_ago INTEGER,
                maintenance_type TEXT,
                issue TEXT,
                note TEXT
            )
        ''')
        
        maint_path = os.path.join(self.data_dir, "maintenance_log.json")
        if os.path.exists(maint_path):
            with open(maint_path, "r") as f:
                maintenance = json.load(f)
                for m in maintenance:
                    cursor.execute('''
                        INSERT INTO maintenance_log 
                        (machine_id, maintenance_date, days_ago, maintenance_type, issue, note)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        m['machine_id'], m['maintenance_date'], m['days_ago'], 
                        m['maintenance_type'], m['issue'], m['note']
                    ))
                    
        # 3. Production Baseline
        cursor.execute('''
            CREATE TABLE machine_baseline (
                machine_id TEXT PRIMARY KEY,
                historical_waste_pct REAL,
                historical_avg_speed REAL,
                historical_avg_qty REAL,
                total_batches INTEGER
            )
        ''')
        
        hist_path = os.path.join(self.data_dir, "historical_production.csv")
        if os.path.exists(hist_path):
            df = pd.read_csv(hist_path)
            # Calculate baselines deterministically from the history
            for m, m_data in df.groupby('Machine ID'):
                if str(m).startswith('M'):
                    waste_pct = (m_data['Waste quantity'] / m_data['Production quantity'] * 100).mean()
                    speed = m_data['Production speed'].mean()
                    qty = m_data['Production quantity'].mean()
                    count = len(m_data)
                    cursor.execute('''
                        INSERT INTO machine_baseline 
                        (machine_id, historical_waste_pct, historical_avg_speed, historical_avg_qty, total_batches)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (m, float(waste_pct), float(speed), float(qty), count))
        
        self.conn.commit()
        
    def get_machine_profile(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the machine's rated limits and profile."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM machine_catalog WHERE machine_id = ?', (machine_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def get_machine_baseline(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the machine's actual historical operating averages."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM machine_baseline WHERE machine_id = ?', (machine_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def get_maintenance_history(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the latest maintenance record for the machine."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM maintenance_log WHERE machine_id = ? ORDER BY days_ago ASC LIMIT 1', (machine_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_machine_ids(self) -> set[str]:
        """Fetch all known machine IDs from the catalog."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT machine_id FROM machine_catalog')
        return {row['machine_id'] for row in cursor.fetchall()}

    def get_all_machines(self) -> list[dict[str, any]]:
        """Fetch all machines with their profiles, baselines, and maintenance history."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM machine_catalog')
        rows = cursor.fetchall()
        machines = []
        for r in rows:
            m = dict(r)
            m['baseline'] = self.get_machine_baseline(m['machine_id'])
            m['maintenance'] = self.get_maintenance_history(m['machine_id'])
            machines.append(m)
        return machines

    def add_machine(self, machine_data: dict[str, any]) -> bool:
        """Add a new machine to the catalog."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO machine_catalog 
            (machine_id, machine_type, rated_capacity, rated_speed, installation_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            machine_data['machine_id'],
            machine_data.get('machine_type', 'Standard Loom'),
            float(machine_data.get('rated_capacity', 1500.0)),
            float(machine_data.get('rated_speed', 1000.0)),
            machine_data.get('installation_date', '2026-01-01'),
            machine_data.get('status', 'Active')
        ))
        self.conn.commit()
        return True

    def close(self):
        self.conn.close()
