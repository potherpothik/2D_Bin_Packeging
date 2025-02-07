import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
from dataclasses import dataclass
from typing import List, Dict, Tuple
from matplotlib.backends.backend_pdf import PdfPages

@dataclass
class Part:
    id: str
    width: float
    height: float
    quantity: int

@dataclass
class StockSize:
    name: str
    width: float
    height: float
    quantity: int

@dataclass
class PackingResult:
    part_id: str
    x: float
    y: float
    width: float
    height: float
    stock_name: str

class FileHandler:
    def __init__(self):
        self.parts_data = None
        self.stock_sizes = None
        self.results = []
        
    def load_parts(self, file_path: str) -> List[Part]:
        """Load parts data from CSV file"""
        try:
            df = pd.read_csv(file_path)
            required_columns = ['id', 'width', 'height', 'quantity']
            
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                raise ValueError(f"Missing columns in parts file: {missing}")
            
            parts = []
            for _, row in df.iterrows():
                for i in range(int(row['quantity'])):
                    parts.append(Part(
                        id=f"{row['id']}_{i+1}",
                        width=float(row['width']),
                        height=float(row['height']),
                        quantity=1
                    ))
            self.parts_data = parts
            return parts
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Parts file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error loading parts file: {str(e)}")

    def load_stock_sizes(self, file_path: str) -> List[StockSize]:
        """Load stock sizes from CSV file"""
        try:
            df = pd.read_csv(file_path)
            required_columns = ['name', 'width', 'height', 'quantity']
            
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                raise ValueError(f"Missing columns in stock size file: {missing}")
            
            stock_sizes = []
            for _, row in df.iterrows():
                stock_sizes.append(StockSize(
                    name=row['name'],
                    width=float(row['width']),
                    height=float(row['height']),
                    quantity=int(row['quantity'])
                ))
            self.stock_sizes = stock_sizes
            return stock_sizes
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Stock sizes file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error loading stock sizes file: {str(e)}")

class BinPacker:
    def __init__(self, parts: List[Part], stock_sizes: List[StockSize]):
        self.parts = sorted(parts, key=lambda x: (x.width * x.height), reverse=True)
        self.stock_sizes = stock_sizes
        self.results: List[PackingResult] = []
        
    def pack(self) -> List[PackingResult]:
        """Simple bottom-left packing algorithm"""
        for stock in self.stock_sizes:
            current_x = 0
            current_y = 0
            max_height_in_row = 0
            
            remaining_parts = self.parts.copy()
            stock_used = 0
            
            while remaining_parts and stock_used < stock.quantity:
                part = remaining_parts[0]
                
                # Check if we need to move to new row
                if current_x + part.width > stock.width:
                    current_x = 0
                    current_y += max_height_in_row
                    max_height_in_row = 0
                
                # Check if we need new stock sheet
                if current_y + part.height > stock.height:
                    current_x = 0
                    current_y = 0
                    max_height_in_row = 0
                    stock_used += 1
                    if stock_used >= stock.quantity:
                        break
                
                # Place the part
                self.results.append(PackingResult(
                    part_id=part.id,
                    x=current_x,
                    y=current_y,
                    width=part.width,
                    height=part.height,
                    stock_name=stock.name
                ))
                
                current_x += part.width
                max_height_in_row = max(max_height_in_row, part.height)
                remaining_parts.pop(0)
            
        return self.results

class ResultHandler:
    def __init__(self, output_path: str):
        self.output_path = output_path
        
    def save_results_pdf(self, results: List[PackingResult], 
                        stock_sizes: List[StockSize]):
        """Save packing results to PDF with visualizations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(
            self.output_path, 
            f"packing_results_{timestamp}.pdf"
        )
        
        # Group results by stock sheet
        results_by_stock = {}
        for result in results:
            if result.stock_name not in results_by_stock:
                results_by_stock[result.stock_name] = []
            results_by_stock[result.stock_name].append(result)
        
        with PdfPages(pdf_path) as pdf:
            # Summary page
            plt.figure(figsize=(11, 8))
            plt.title("Packing Summary")
            summary_text = [
                "Bin Packing Results Summary",
                f"Total parts packed: {len(results)}",
                f"Stock sizes used: {len(results_by_stock)}",
                "\nStock Sheets Usage:",
            ]
            for stock_name, stock_results in results_by_stock.items():
                summary_text.append(
                    f"- {stock_name}: {len(stock_results)} parts"
                )
            
            plt.text(0.1, 0.9, "\n".join(summary_text), 
                    transform=plt.gca().transAxes)
            plt.axis('off')
            pdf.savefig()
            plt.close()
            
            # Visualization pages for each stock sheet
            for stock_name, stock_results in results_by_stock.items():
                stock_size = next(s for s in stock_sizes 
                                if s.name == stock_name)
                
                plt.figure(figsize=(11, 8))
                plt.title(f"Layout for {stock_name}")
                
                # Draw each part
                for result in stock_results:
                    rect = plt.Rectangle(
                        (result.x, result.y),
                        result.width,
                        result.height,
                        fill=True,
                        facecolor='lightblue',
                        edgecolor='black'
                    )
                    plt.gca().add_patch(rect)
                    
                    # Add part ID label
                    plt.text(
                        result.x + result.width/2,
                        result.y + result.height/2,
                        result.part_id,
                        ha='center',
                        va='center'
                    )
                
                plt.xlim(0, stock_size.width)
                plt.ylim(0, stock_size.height)
                plt.grid(True)
                pdf.savefig()
                plt.close()
        
        return pdf_path

def main():
    # Set your file paths here
    PARTS_FILE = "path/to/your/parts.csv"
    STOCK_FILE = "path/to/your/stock.csv"
    OUTPUT_DIR = "path/to/your/output"
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        # Initialize handlers
        file_handler = FileHandler()
        
        # Load input files
        parts = file_handler.load_parts(PARTS_FILE)
        stock_sizes = file_handler.load_stock_sizes(STOCK_FILE)
        
        # Run packing algorithm
        packer = BinPacker(parts, stock_sizes)
        results = packer.pack()
        
        # Save results
        result_handler = ResultHandler(OUTPUT_DIR)
        pdf_path = result_handler.save_results_pdf(results, stock_sizes)
        
        print(f"Packing completed successfully!")
        print(f"Results saved to: {pdf_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
