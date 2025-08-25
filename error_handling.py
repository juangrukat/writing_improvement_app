#!/usr/bin/env python3
"""
Error handling module for the Writing Improvement App.
Provides robust error handling and user-friendly error messages.
"""

import tkinter as tk
from tkinter import messagebox
import sqlite3
import os


class ErrorHandler:
    """Handles application errors and provides user-friendly messages."""
    
    @staticmethod
    def handle_database_error(error, operation="database operation"):
        """Handle database-related errors."""
        error_msg = f"Database error during {operation}: {str(error)}"
        print(f"ERROR: {error_msg}")
        
        if isinstance(error, sqlite3.OperationalError):
            if "no such table" in str(error):
                return "Database structure error. Please restart the application."
            elif "database is locked" in str(error):
                return "Database is busy. Please try again."
        
        return f"Database operation failed: {str(error)}"
    
    @staticmethod
    def handle_file_error(error, operation="file operation", filename=""):
        """Handle file-related errors."""
        error_msg = f"File error during {operation}"
        if filename:
            error_msg += f" with file '{filename}'"
        error_msg += f": {str(error)}"
        print(f"ERROR: {error_msg}")
        
        if isinstance(error, FileNotFoundError):
            return f"File not found: {filename}"
        elif isinstance(error, PermissionError):
            return f"Permission denied for file: {filename}"
        elif isinstance(error, IsADirectoryError):
            return f"Expected a file but found a directory: {filename}"
        
        return f"File operation failed: {str(error)}"
    
    @staticmethod
    def handle_import_error(error, operation="import operation"):
        """Handle import-related errors."""
        error_msg = f"Import error during {operation}: {str(error)}"
        print(f"ERROR: {error_msg}")
        
        if "pandas" in str(error):
            return "Pandas library not available. CSV import/export features disabled."
        
        return f"Import operation failed: {str(error)}"
    
    @staticmethod
    def show_error_dialog(parent, title, message):
        """Show an error dialog to the user."""
        messagebox.showerror(title, message, parent=parent)
    
    @staticmethod
    def show_warning_dialog(parent, title, message):
        """Show a warning dialog to the user."""
        messagebox.showwarning(title, message, parent=parent)
    
    @staticmethod
    def show_info_dialog(parent, title, message):
        """Show an information dialog to the user."""
        messagebox.showinfo(title, message, parent=parent)


def safe_database_operation(func):
    """Decorator for safe database operations with error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()
            error_msg = error_handler.handle_database_error(e, func.__name__)
            # If we have a parent window in args, show dialog
            for arg in args:
                if isinstance(arg, tk.Tk) or isinstance(arg, tk.Toplevel):
                    error_handler.show_error_dialog(arg, "Database Error", error_msg)
                    break
            return None
    return wrapper


def safe_file_operation(func):
    """Decorator for safe file operations with error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()
            filename = kwargs.get('filename', kwargs.get('file_path', ''))
            error_msg = error_handler.handle_file_error(e, func.__name__, filename)
            # If we have a parent window in args, show dialog
            for arg in args:
                if isinstance(arg, tk.Tk) or isinstance(arg, tk.Toplevel):
                    error_handler.show_error_dialog(arg, "File Error", error_msg)
                    break
            return None
    return wrapper
