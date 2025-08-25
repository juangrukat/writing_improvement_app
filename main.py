#!/usr/bin/env python3
"""
Writing Improvement App - Main Application
A tool to help users improve writing through sentence rewriting practice.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import pandas as pd
import random
import os
from datetime import datetime
from typing import List, Optional, Tuple


class WritingAppModel:
    """Model layer for database operations and data management."""
    
    def __init__(self, db_path: str = "writing_app.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentences (
                    id INTEGER PRIMARY KEY,
                    original TEXT NOT NULL,
                    rewrite TEXT,
                    seen BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            conn.commit()
    
    def import_csv(self, file_path: str) -> int:
        """Import sentences from CSV file with duplicate checking."""
        try:
            df = pd.read_csv(file_path)
            if 'sentence' not in df.columns:
                raise ValueError("CSV must contain a 'sentence' column")
            
            imported_count = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for _, row in df.iterrows():
                    sentence = str(row['sentence']).strip()
                    if not sentence:
                        continue
                    
                    # Check for duplicates
                    cursor.execute(
                        "SELECT id FROM sentences WHERE original = ?", 
                        (sentence,)
                    )
                    if cursor.fetchone() is None:
                        cursor.execute(
                            "INSERT INTO sentences (original) VALUES (?)",
                            (sentence,)
                        )
                        imported_count += 1
                
                conn.commit()
            
            return imported_count
            
        except Exception as e:
            raise Exception(f"Failed to import CSV: {str(e)}")
    
    def get_random_unseen_sentence(self) -> Optional[Tuple[int, str]]:
        """Get a random unseen sentence from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, original FROM sentences WHERE seen = 0 ORDER BY RANDOM() LIMIT 1"
            )
            result = cursor.fetchone()
            return result
    
    def mark_sentence_seen(self, sentence_id: int):
        """Mark a sentence as seen."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sentences SET seen = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (sentence_id,)
            )
            conn.commit()
    
    def save_rewrite(self, sentence_id: int, rewrite: str):
        """Save user's rewrite for a sentence."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sentences SET rewrite = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (rewrite, sentence_id)
            )
            conn.commit()
    
    def get_progress_stats(self) -> Tuple[int, int]:
        """Get progress statistics: total sentences and completed count."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sentences")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sentences WHERE rewrite IS NOT NULL")
            completed = cursor.fetchone()[0]
            
            return total, completed
    
    def export_rewrites_to_csv(self, file_path: str):
        """Export all rewrites to CSV file."""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(
                "SELECT id, original, rewrite, created_at, updated_at FROM sentences WHERE rewrite IS NOT NULL",
                conn
            )
            df.to_csv(file_path, index=False)
    
    def reset_session(self):
        """Reset all sentences to unseen state."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sentences SET seen = 0, rewrite = NULL, updated_at = NULL")
            conn.commit()


class WritingAppView:
    """View layer for the Tkinter UI."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Writing Improvement App")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        self._setup_styles()
        self._create_widgets()
    
    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 11))
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
    
    def _create_widgets(self):
        """Create all UI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Writing Improvement Practice", style="Title.TLabel")
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Progress display
        self.progress_label = ttk.Label(main_frame, text="Progress: 0/0")
        self.progress_label.grid(row=1, column=0, pady=(0, 20))
        
        # Original sentence display
        sentence_frame = ttk.Frame(main_frame)
        sentence_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        sentence_frame.columnconfigure(0, weight=1)
        
        ttk.Label(sentence_frame, text="Original Sentence:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.sentence_text = tk.Text(sentence_frame, height=4, width=60, wrap=tk.WORD, 
                                   font=("Helvetica", 11), relief=tk.FLAT, bg="#f8f8f8")
        self.sentence_text.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.sentence_text.config(state=tk.DISABLED)
        
        # Rewrite input
        ttk.Label(sentence_frame, text="Your Rewrite:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.rewrite_text = tk.Text(sentence_frame, height=6, width=60, wrap=tk.WORD, 
                                  font=("Helvetica", 11))
        self.rewrite_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=(20, 0))
        
        self.import_btn = ttk.Button(button_frame, text="Import CSV")
        self.import_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.save_btn = ttk.Button(button_frame, text="Save & Next")
        self.save_btn.grid(row=0, column=1, padx=10)
        
        self.skip_btn = ttk.Button(button_frame, text="Skip")
        self.skip_btn.grid(row=0, column=2, padx=10)
        
        self.export_btn = ttk.Button(button_frame, text="Export")
        self.export_btn.grid(row=0, column=3, padx=10)
        
        self.reset_btn = ttk.Button(button_frame, text="Reset Session")
        self.reset_btn.grid(row=0, column=4, padx=(10, 0))
    
    def set_sentence_text(self, text: str):
        """Set the original sentence text."""
        self.sentence_text.config(state=tk.NORMAL)
        self.sentence_text.delete(1.0, tk.END)
        self.sentence_text.insert(1.0, text)
        self.sentence_text.config(state=tk.DISABLED)
    
    def get_rewrite_text(self) -> str:
        """Get the user's rewrite text."""
        return self.rewrite_text.get(1.0, tk.END).strip()
    
    def clear_rewrite_text(self):
        """Clear the rewrite text area."""
        self.rewrite_text.delete(1.0, tk.END)
    
    def update_progress(self, completed: int, total: int):
        """Update the progress display."""
        self.progress_label.config(text=f"Progress: {completed}/{total}")
    
    def show_message(self, title: str, message: str):
        """Show a message box."""
        messagebox.showinfo(title, message)
    
    def show_error(self, title: str, message: str):
        """Show an error message box."""
        messagebox.showerror(title, message)
    
    def ask_file_open(self, title: str, filetypes: list) -> Optional[str]:
        """Show file open dialog."""
        return filedialog.askopenfilename(title=title, filetypes=filetypes)
    
    def ask_file_save(self, title: str, filetypes: list) -> Optional[str]:
        """Show file save dialog."""
        return filedialog.asksaveasfilename(title=title, filetypes=filetypes, defaultextension=".csv")


class WritingAppController:
    """Controller layer that orchestrates the application logic."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.model = WritingAppModel()
        self.view = WritingAppView(self.root)
        
        self.current_sentence_id = None
        self.current_sentence_text = None
        
        self._setup_event_handlers()
        self._load_next_sentence()
    
    def _setup_event_handlers(self):
        """Set up event handlers for UI components."""
        self.view.import_btn.config(command=self._handle_import)
        self.view.save_btn.config(command=self._handle_save)
        self.view.skip_btn.config(command=self._handle_skip)
        self.view.export_btn.config(command=self._handle_export)
        self.view.reset_btn.config(command=self._handle_reset)
    
    def _handle_import(self):
        """Handle CSV import."""
        file_path = self.view.ask_file_open(
            "Select CSV file to import",
            [("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                imported_count = self.model.import_csv(file_path)
                self.view.show_message(
                    "Import Successful",
                    f"Successfully imported {imported_count} sentences."
                )
                self._load_next_sentence()
            except Exception as e:
                self.view.show_error("Import Failed", str(e))
    
    def _handle_save(self):
        """Handle save and next operation."""
        if not self.current_sentence_id:
            return
        
        rewrite = self.view.get_rewrite_text()
        if not rewrite:
            self.view.show_error("Error", "Please write something before saving.")
            return
        
        try:
            self.model.save_rewrite(self.current_sentence_id, rewrite)
            self.model.mark_sentence_seen(self.current_sentence_id)
            self.view.clear_rewrite_text()
            self._load_next_sentence()
        except Exception as e:
            self.view.show_error("Save Failed", str(e))
    
    def _handle_skip(self):
        """Handle skip operation."""
        if self.current_sentence_id:
            self.model.mark_sentence_seen(self.current_sentence_id)
            self.view.clear_rewrite_text()
            self._load_next_sentence()
    
    def _handle_export(self):
        """Handle export operation."""
        file_path = self.view.ask_file_save(
            "Export rewrites to CSV",
            [("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                self.model.export_rewrites_to_csv(file_path)
                self.view.show_message(
                    "Export Successful",
                    f"Rewrites exported to {file_path}"
                )
            except Exception as e:
                self.view.show_error("Export Failed", str(e))
    
    def _handle_reset(self):
        """Handle session reset."""
        if messagebox.askyesno(
            "Reset Session",
            "Are you sure you want to reset the session? This will mark all sentences as unseen and clear all rewrites."
        ):
            self.model.reset_session()
            self.view.clear_rewrite_text()
            self._load_next_sentence()
    
    def _load_next_sentence(self):
        """Load the next random unseen sentence."""
        sentence_data = self.model.get_random_unseen_sentence()
        
        if sentence_data:
            self.current_sentence_id, self.current_sentence_text = sentence_data
            self.view.set_sentence_text(self.current_sentence_text)
        else:
            self.current_sentence_id = None
            self.current_sentence_text = None
            self.view.set_sentence_text("No more sentences to practice! Import more or reset the session.")
        
        # Update progress
        total, completed = self.model.get_progress_stats()
        self.view.update_progress(completed, total)
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Main entry point for the application."""
    app = WritingAppController()
    app.run()


if __name__ == "__main__":
    main()
