import pandas as pd
import numpy as np
from typing import List, Tuple

class GlassPiece:
    def __init__(self, location: str, length: float, height: float, qty: int):
        self.location = location
        self.length = length
        self.height = height
        self.qty = qty
        self.area = length * height / 1_000_000  # Convert mm to sqm

class StockSheet:
    def __init__(self, length: float, width: float):
        self.length = length
        self.width = width
        self.total_area = length * width / 1_000_000  # Convert mm to sqm

class HybridGlassCuttingOptimizer:
    def __init__(self, stock_sheets: List[StockSheet], glass_pieces: List[GlassPiece]):
        self.stock_sheets = stock_sheets
        self.glass_pieces = glass_pieces
        
    def optimize(self):
        # Sort pieces by area in descending order
        sorted_pieces = sorted(
            [piece for piece in self.glass_pieces for _ in range(piece.qty)],
            key=lambda p: p.length * p.height, 
            reverse=True
        )
        
        # Track utilization
        sheet_utilization = []
        remaining_pieces = sorted_pieces.copy()
        
        for stock_sheet in self.stock_sheets:
            sheet_cuts = self._optimize_single_sheet(stock_sheet, remaining_pieces)
            
            if sheet_cuts:
                sheet_util = sum(cut.length * cut.height for cut in sheet_cuts) / stock_sheet.total_area
                sheet_utilization.append({
                    'sheet_size': f"{stock_sheet.length}x{stock_sheet.width}",
                    'utilized_pieces': len(sheet_cuts),
                    'utilization_percentage': sheet_util * 100
                })
                
                # Remove used pieces
                for cut in sheet_cuts:
                    remaining_pieces.remove(cut)
        
        return {
            'sheet_utilization': sheet_utilization,
            'remaining_pieces': len(remaining_pieces)
        }
    
    def _optimize_single_sheet(self, stock_sheet, pieces):
        sheet_cuts = []
        remaining_pieces = pieces.copy()
        
        while remaining_pieces:
            best_piece = None
            best_efficiency = 0
            
            for piece in remaining_pieces:
                # Check if piece can fit in the stock sheet
                if (piece.length <= stock_sheet.length and piece.height <= stock_sheet.width) or \
                   (piece.height <= stock_sheet.length and piece.length <= stock_sheet.width):
                    
                    # Calculate potential efficiency
                    piece_area = piece.length * piece.height
                    sheet_area = stock_sheet.length * stock_sheet.width
                    efficiency = piece_area / sheet_area
                    
                    if efficiency > best_efficiency:
                        best_piece = piece
                        best_efficiency = efficiency
            
            if best_piece:
                sheet_cuts.append(best_piece)
                remaining_pieces.remove(best_piece)
            else:
                break
        
        return sheet_cuts

def main():
    # Read input data
    glass_data = pd.read_csv('glass_data.csv')
    stock_data = pd.read_csv('glass_sheet_size.csv')
    
    # Prepare glass pieces
    glass_pieces = [
        GlassPiece(
            location=row['location'], 
            length=row['glass_length'], 
            height=row['glass_height'], 
            qty=row['glass_qty']
        ) for _, row in glass_data.iterrows()
    ]
    
    # Prepare stock sheets
    stock_sheets = [
        StockSheet(length=row['length'], width=row['width']) 
        for _, row in stock_data.iterrows() 
        for _ in range(row['qty'])
    ]
    
    # Create optimizer
    optimizer = HybridGlassCuttingOptimizer(stock_sheets, glass_pieces)
    
    # Run optimization
    results = optimizer.optimize()
    
    # Print results
    print("Sheet Utilization Results:")
    for sheet in results['sheet_utilization']:
        print(f"Sheet Size: {sheet['sheet_size']}")
        print(f"Utilized Pieces: {sheet['utilized_pieces']}")
        print(f"Utilization Percentage: {sheet['utilization_percentage']:.2f}%\n")
    
    print(f"Remaining Uncut Pieces: {results['remaining_pieces']}")

if __name__ == "__main__":
    main()
