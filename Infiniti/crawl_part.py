import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os

class PartsouqHTMLSaver:
    def __init__(self):
        # Setup undetected Chrome để bypass Cloudflare
        options = uc.ChromeOptions()
        # options.add_argument('--headless=new')  # Uncomment để chạy ngầm
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = uc.Chrome(options=options, version_main=None)
        self.base_url = "https://partsouq.com"
        
        # Tạo thư mục lưu HTML
        self.html_folder = 'html_sources'
        os.makedirs(self.html_folder, exist_ok=True)
    
    def load_json(self, filename):
        """Load data from JSON file"""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_json(self, data, filename):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu index file: {filename}")
    
    def _safe_filename(self, name):
        """Chuyển tên thành tên file an toàn"""
        safe = name.replace('/', '').replace('\\', '').replace(':', '_')
        safe = safe.replace('*', '').replace('?', '').replace('"', '_')
        safe = safe.replace('<', '').replace('>', '').replace('|', '_')
        safe = safe.replace(' ', '_').strip()
        
        if len(safe) > 100:
            safe = safe[:100]
        
        return safe
    
    def save_html(self, url, brand, car_type, model, category, title):
        """Truy cập URL, lưu HTML VÀ crawl parts"""
        try:
            print(f"          🌐 Đang truy cập: {url}")
            self.driver.get(url)
            
            # Chờ Cloudflare
            time.sleep(3)
            
            # Wait for page load
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table-bordered-1")))
            
            # Lấy HTML source
            html_content = self.driver.page_source
            
            # Tạo thư mục theo cấu trúc
            folder_path = os.path.join(
                self.html_folder,
                self._safe_filename(brand),
                self._safe_filename(car_type),
                self._safe_filename(model),
                self._safe_filename(category)
            )
            os.makedirs(folder_path, exist_ok=True)
            
            # Tạo tên file
            filename = self._safe_filename(title) + '.html'
            filepath = os.path.join(folder_path, filename)
            
            # Lưu HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Return đường dẫn tương đối
            relative_path = os.path.relpath(filepath, '.')
            print(f"          ✅ HTML: {relative_path}")
            
            # CRAWL PARTS DATA
            parts = self._parse_parts()
            print(f"          ✅ Parts: {len(parts)} items")
            
            return relative_path, parts
            
        except Exception as e:
            print(f"          ❌ Lỗi: {e}")
            return None, []
    
    def _parse_parts(self):
        """Parse parts từ trang hiện tại"""
        try:
            parts = []
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".table-bordered-1 tbody tr.part-search-tr")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 6:
                        # Extract part number
                        number_cell = cells[0]
                        number_link = number_cell.find_elements(By.TAG_NAME, "a")
                        number = number_link[0].text.strip() if number_link else number_cell.text.strip()
                        
                        # Extract other data
                        name = cells[1].text.strip()
                        code = cells[2].text.strip()
                        note = cells[3].text.strip()
                        quantity = cells[4].text.strip()
                        range_val = cells[5].text.strip()
                        
                        parts.append({
                            "number": number,
                            "name": name,
                            "code": code,
                            "note": note,
                            "quantity": quantity,
                            "range": range_val
                        })
                except:
                    continue
            
            return parts
        except:
            return []
    
    def save_all_html_from_json(self, input_file, output_file):
        """Lưu HTML cho tất cả URLs trong JSON VÀ cập nhật cấu trúc JSON gốc"""
        print("="*80)
        print("🚀 BẮT ĐẦU LƯU HTML + CRAWL PARTS")
        print("="*80)
        
        # Load JSON data
        print(f"\n📂 Đang đọc file: {input_file}")
        data = self.load_json(input_file)
        
        total_saved = 0
        total_failed = 0
        total_parts = 0
        
        # Loop through brands
        for brand in data:
            brand_name = brand['brand']
            print(f"\n🏢 Brand: {brand_name}")
            
            # Loop through car types
            for car_type in brand.get('car_types', []):
                car_type_name = car_type['car_type']
                print(f"\n  📦 Car Type: {car_type_name}")
                
                # Loop through models
                for model in car_type.get('models', []):
                    model_name = model['model']
                    print(f"\n    🚙 Model: {model_name}")
                    
                    # Loop through categories
                    for category in model.get('categories', []):
                        category_name = category['category']
                        print(f"\n      📁 Category: {category_name}")
                        print(f"         Titles: {len(category.get('titles', []))}")
                        
                        # Loop through titles
                        for idx, title in enumerate(category.get('titles', []), 1):
                            title_name = title['title']
                            title_url = title['url']
                            
                            print(f"\n        [{idx}/{len(category['titles'])}] ⚙️  {title_name}")
                            
                            # Lưu HTML VÀ crawl parts
                            html_file, parts = self.save_html(
                                title_url,
                                brand_name,
                                car_type_name,
                                model_name,
                                category_name,
                                title_name
                            )
                            
                            if html_file:
                                # CẬP NHẬT VÀO CẤU TRÚC GỐC
                                title['html_file'] = html_file
                                title['parts'] = parts
                                total_saved += 1
                                total_parts += len(parts)
                            else:
                                title['html_file'] = None
                                title['parts'] = []
                                total_failed += 1
        
        # Save updated data (GIỮ NGUYÊN CẤU TRÚC GỐC)
        print(f"\n{'='*80}")
        print(f"✅ HOÀN THÀNH")
        print(f"{'='*80}")
        print(f"📊 Tổng số HTML đã lưu: {total_saved}")
        print(f"📊 Tổng số parts đã crawl: {total_parts}")
        print(f"📊 Tổng số thất bại: {total_failed}")
        
        self.save_json(data, output_file)
        print(f"📂 File output: {output_file}")
        print(f"📂 Thư mục HTML: {self.html_folder}/")
    
    def close(self):
        """Close browser"""
        self.driver.quit()


# Main execution
if __name__ == "__main__":
    saver = PartsouqHTMLSaver()
    
    try:
        # Input: file JSON có titles và URLs
        input_file = "Toyota_Progress_CT1.json"
        
        # Output: file JSON index mapping URL -> HTML file
        index_file = "Toyota_HTML_Index.json"
        
        # Lưu HTML cho tất cả URLs
        saver.save_all_html_from_json(input_file, index_file)
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🔒 Đóng browser...")
        saver.close()
    
    print("\n✨ HOÀN THÀNH!")