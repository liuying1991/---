"""Run Logger — SQLite-based logging for simulation runs."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Optional


class RunLogger:
    """
    SQLite logger for simulation runs.
    """

    def __init__(self, db_path: str = "data/runs.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS cycles (
                cycle_id INTEGER,
                sim_hours REAL,
                stage TEXT,
                node_count INTEGER,
                connection_count INTEGER,
                total_energy REAL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS node_snapshots (
                cycle_id INTEGER,
                node_id TEXT,
                type TEXT,
                activation REAL,
                energy REAL,
                plasticity REAL,
                n_connections INTEGER
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS type_counts (
                cycle_id INTEGER,
                stem INTEGER DEFAULT 0,
                sensor INTEGER DEFAULT 0,
                interneuron INTEGER DEFAULT 0,
                inhibitor INTEGER DEFAULT 0,
                oscillator INTEGER DEFAULT 0,
                projector INTEGER DEFAULT 0,
                hub INTEGER DEFAULT 0,
                memory INTEGER DEFAULT 0,
                gate INTEGER DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS metric_results (
                run_id TEXT,
                metric_name TEXT,
                value REAL,
                passed INTEGER
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                seed_name TEXT,
                sim_hours REAL,
                final_node_count INTEGER,
                weighted_score REAL,
                teii REAL,
                all_passed INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def log_cycle(self, cycle: int, sim_hours: float, stage: str,
                  network):
        """Log cycle summary to database."""
        stats = network.global_stats
        type_counts = stats.type_counts

        c = self.conn.cursor()
        c.execute(
            'INSERT INTO cycles VALUES (?, ?, ?, ?, ?, ?)',
            (cycle, sim_hours, stage, stats.node_count,
             stats.total_edges, stats.total_energy)
        )

        # Type counts
        c.execute(
            'INSERT INTO type_counts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (cycle,
             type_counts.get('STEM', 0),
             type_counts.get('SENSOR', 0),
             type_counts.get('INTERNEURON', 0),
             type_counts.get('INHIBITOR', 0),
             type_counts.get('OSCILLATOR', 0),
             type_counts.get('PROJECTOR', 0),
             type_counts.get('HUB', 0),
             type_counts.get('MEMORY', 0),
             type_counts.get('GATE', 0))
        )

        # Node snapshots (every 1000 cycles to avoid bloat)
        if cycle % 1000 == 0:
            for node_id, node in network.nodes.items():
                c.execute(
                    'INSERT INTO node_snapshots VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (cycle, node_id, node.type.value, node.activation,
                     node.energy, node.plasticity, len(node.connections))
                )

        self.conn.commit()

    def log_run(self, run_id: str, seed_name: str, sim_hours: float,
                final_node_count: int, weighted_score: float,
                teii: float, all_passed: bool):
        """Log run summary."""
        c = self.conn.cursor()
        c.execute(
            'INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)',
            (run_id, seed_name, sim_hours, final_node_count,
             weighted_score, teii, int(all_passed))
        )
        self.conn.commit()

    def log_metrics(self, run_id: str, metrics_result):
        """Log individual metric results."""
        c = self.conn.cursor()
        passed_dict = metrics_result.passed_metrics()

        for metric_name in ['self_sustain', 'learning', 'discrimination',
                            'generalization', 'persistence', 'self_awareness',
                            'metaplasticity']:
            value = getattr(metrics_result, metric_name, 0.0)
            passed = int(passed_dict.get(metric_name, False))
            c.execute(
                'INSERT INTO metric_results VALUES (?, ?, ?, ?)',
                (run_id, metric_name, value, passed)
            )

        self.conn.commit()

    def export_csv(self, table_name: str, output_path: str = None) -> str:
        """Export a table to CSV. Returns the output file path."""
        if output_path is None:
            output_path = self.db_path.replace('.db', f'_{table_name}.csv')

        c = self.conn.cursor()
        c.execute(f'SELECT * FROM {table_name}')
        rows = c.fetchall()
        columns = [desc[0] for desc in c.description]

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)

        return output_path

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
