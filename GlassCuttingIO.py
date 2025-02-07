import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
from datetime import datetime

@dataclass
class Panel:
    length: float
    height: float
    quantity: int
    location: str
    area_sqm: float

@dataclass
class Stock:
    length: float
    width: float
    quantity: int

class GlassCuttingIO:
    @staticmethod
    def load_stock_sizes(file_path: str) -> List[Stock]:
        """Load stock sizes from CSV file"""
        try:
            df = pd.read_csv(file_path)
            stocks = []
            for _, row in df.iterrows():
                stock = Stock(
                    length=float(row['length']),
                    width=float(row['width']),
                    quantity=int(row['qty'])
                )
                stocks.append(stock)
            return stocks
        except FileNotFoundError:
            raise FileNotFoundError(f"Stock sizes file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error loading stock sizes: {str(e)}")

    @staticmethod
    def load_glass_data(file_path: str) -> List[Panel]:
        """Load panel requirements from CSV file"""
        try:
            df = pd.read_csv(file_path)
            panels = []
            for _, row in df.iterrows():
                panel = Panel(
                    length=float(row['glass_length']),
                    height=float(row['glass_height']),
                    quantity=int(row['glass_qty']),
                    location=str(row['location']),
                    area_sqm=float(row['area_sqm'])
                )
                panels.append(panel)
            return panels
        except FileNotFoundError:
            raise FileNotFoundError(f"Glass data file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error loading glass data: {str(e)}")

class OptimizationResult:
    def __init__(self, placements: List[Tuple], total_sheets: dict, efficiency: float):
        self.placements = placements
        self.total_sheets = total_sheets
        self.efficiency = efficiency

class GlassCuttingOptimizer:
    def __init__(self, stocks: List[Stock], cut_width: float = 5):  # 5mm cutting width
        self.stocks = stocks
        self.cut_width = cut_width
        
    def optimize(self, panels: List[Panel]) -> OptimizationResult:
        """Optimize cutting layout for all panels"""
        all_placements = []
        sheets_used = {f"{stock.length}x{stock.width}": 0 for stock in self.stocks}
        total_panel_area = 0
        total_sheet_area = 0
        
        # Sort panels by height in descending order
        sorted_panels = []
        for panel in panels:
            for _ in range(panel.quantity):
                sorted_panels.append((panel.length, panel.height, panel.location))
        sorted_panels.sort(key=lambda x: (x[1], x[0]), reverse=True)
        
        current_stock_idx = 0
        current_sheet = 0
        x, y = 0, 0
        max_height = 0
        
        for panel_length, panel_height, location in sorted_panels:
            placed = False
            
            while not placed:
                stock = self.stocks[current_stock_idx]
                
                # Add cutting width
                effective_length = panel_length + self.cut_width
                effective_height = panel_height + self.cut_width
                
                # Try to place panel in current position
                if (x + effective_length <= stock.length and 
                    y + effective_height <= stock.width):
                    all_placements.append({
                        'location': location,
                        'x': x,
                        'y': y,
                        'length': panel_length,
                        'height': panel_height,
                        'sheet_size': f"{stock.length}x{stock.width}",
                        'sheet_number': current_sheet
                    })
                    
                    max_height = max(max_height, effective_height)
                    x += effective_length
                    total_panel_area += panel_length * panel_height
                    placed = True
                
                # Try next row
                elif x > 0 and y + max_height + effective_height <= stock.width:
                    x = 0
                    y += max_height
                    max_height = 0
                    continue
                
                # Try next sheet
                else:
                    sheets_used[f"{stock.length}x{stock.width}"] += 1
                    total_sheet_area += stock.length * stock.width
                    
                    # Check if we need to switch to a different stock size
                    if sheets_used[f"{stock.length}x{stock.width}"] >= stock.quantity:
                        current_stock_idx += 1
                        if current_stock_idx >= len(self.stocks):
                            raise ValueError("Not enough stock sheets available")
                    
                    current_sheet += 1
                    x, y = 0, 0
                    max_height = 0
                    continue
        
        # Add last sheet to total
        if x > 0 or y > 0:
            sheets_used[f"{stock.length}x{stock.width}"] += 1
            total_sheet_area += stock.length * stock.width
        
        efficiency = (total_panel_area / total_sheet_area) * 100
        return OptimizationResult(all_placements, sheets_used, efficiency)

    def export_visualization(self, result: OptimizationResult, output_dir: str = 'output'):
        """Export cutting layout visualization to PDF"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = os.path.join(output_dir, f'glass_cutting_layout_{timestamp}.pdf')
        
        with PdfPages(pdf_path) as pdf:
            # Summary page
            plt.figure(figsize=(11.7, 8.3))  # A4 landscape
            plt.axis('off')
            
            summary_text = [
                "Glass Cutting Optimization Summary",
                "=" * 50,
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Overall Efficiency: {result.efficiency:.1f}%",
                "\nStock Sheets Used:",
            ]
            
            for size, count in result.total_sheets.items():
                if count > 0:
                    length, width = map(float, size.split('x'))
                    summary_text.append(
                        f"- {count} sheets of {length}mm × {width}mm"
                    )
            
            plt.text(0.1, 0.95, '\n'.join(summary_text),
                    transform=plt.gca().transAxes,
                    fontsize=10, family='monospace',
                    verticalalignment='top')
            
            pdf.savefig()
            plt.close()
            
            # Cutting layouts by sheet
            sheet_groups = {}
            for placement in result.placements:
                key = (placement['sheet_size'], placement['sheet_number'])
                if key not in sheet_groups:
                    sheet_groups[key] = []
                sheet_groups[key].append(placement)
            
            for (sheet_size, sheet_number), placements in sheet_groups.items():
                length, width = map(float, sheet_size.split('x'))
                
                # Calculate figure size to maintain aspect ratio
                fig_width = min(11.7, length / 200)  # A4 landscape width in inches
                fig_height = fig_width * (width / length)
                
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                
                # Draw stock sheet
                ax.add_patch(plt.Rectangle((0, 0), length, width,
                                         fill=False, color='black'))
                
                # Draw panels
                colors = plt.cm.Set3(np.linspace(0, 1, len(placements)))
                for placement, color in zip(placements, colors):
                    ax.add_patch(plt.Rectangle(
                        (placement['x'], placement['y']),
                        placement['length'],
                        placement['height'],
                        fill=True,
                        color=color,
                        alpha=0.5
                    ))
                    
                    # Add label
                    ax.text(
                        placement['x'] + placement['length']/2,
                        placement['y'] + placement['height']/2,
                        f"{placement['location']}\n{placement['length']}×{placement['height']}",
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=8,
                        wrap=True
                    )
                
                ax.set_xlim(-50, length + 50)
                ax.set_ylim(-50, width + 50)
                ax.set_aspect('equal')
                ax.set_title(f'Sheet {sheet_number + 1} ({sheet_size}mm)')
                
                # Add dimensions
                ax.text(length/2, -30, f'{length}mm', horizontalalignment='center')
                ax.text(-30, width/2, f'{width}mm', verticalalignment='center',
                       rotation=90)
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
        
        print(f"PDF exported to: {pdf_path}")
        return pdf_path