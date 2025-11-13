import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os

class PartsouqHTMLSaver:
    def __init__(self):
        # Setup undetected Chrome 
        options = uc.ChromeOptions()
        # options.add_argument('--headless=new')  
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = uc.Chrome(options=options, version_main=None)
        self.base_url = "https://partsouq.com"
        
        # Tạo thư mục lưu HTML
        self.html_folder = 'html_sources'
        os.makedirs(self.html_folder, exist_ok=True)
        
        # Thư mục backup
        self.backup_folder = 'backups'
        os.makedirs(self.backup_folder, exist_ok=True)
        
        # Tracking folder đã dùng để tránh trùng
        self.used_folders = {}
        self.current_model_folder = None  # Track folder hiện tại của model
    
    def load_json(self, filename):
        """Load data from JSON file"""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_json(self, data, filename):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã lưu file: {filename}")
    
    def save_backup(self, data, brand_name, car_type_idx, model_idx):
        """Lưu backup sau mỗi model"""
        safe_brand = self._safe_filename(brand_name)
        
        backup_filename = f"{safe_brand}_CarType{car_type_idx}_Model{model_idx}.json"
        backup_path = os.path.join(self.backup_folder, backup_filename)
        
        self.save_json(data, backup_path)
        print(f"💾 BACKUP: {backup_path}")
    
    def set_current_model_folder(self, brand, car_type, model):
        """Set folder cho model hiện tại - gọi 1 lần khi bắt đầu model mới"""
        base_model_folder = os.path.join(
            self.html_folder,
            self._safe_filename(brand),
            self._safe_filename(car_type),
            self._safe_filename(model)
        )
        
        # Check unique và lưu lại
        self.current_model_folder = self._get_unique_folder(base_model_folder)
        print(f"  📁 Model folder: {self.current_model_folder}")
    
    def _get_unique_folder(self, base_path):
        """Tạo tên thư mục unique nếu bị trùng - CHỈ CHECK 1 LẦN"""
        # Nếu chưa xử lý path này bao giờ
        if base_path not in self.used_folders:
            # Check xem folder có tồn tại không
            if not os.path.exists(base_path):
                # Chưa tồn tại -> dùng tên gốc
                self.used_folders[base_path] = base_path
                return base_path
            else:
                # Đã tồn tại -> tìm số tiếp theo
                counter = 1
                while True:
                    new_path = f"{base_path}{counter}"
                    if not os.path.exists(new_path):
                        self.used_folders[base_path] = new_path
                        return new_path
                    counter += 1
        
        # Đã xử lý rồi -> trả về kết quả đã lưu
        return self.used_folders[base_path]
    
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
            print(f"      🌐 Đang truy cập: {url}")
            self.driver.get(url)
            
            # Chờ Cloudflare
            print(f"      ⏳ Chờ Cloudflare...")
            time.sleep(3)
            
            # Wait for page load
            print(f"      ⏳ Chờ load trang...")
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".table-bordered-1")))
            
            # Lấy HTML source
            html_content = self.driver.page_source
            
            # Dùng folder đã set sẵn cho model hiện tại
            if not self.current_model_folder:
                raise Exception("Chưa set current_model_folder! Gọi set_current_model_folder() trước.")
            
            # Tạo đường dẫn đầy đủ: brand/car_type/model/category
            folder_path = os.path.join(
                self.current_model_folder,
                self._safe_filename(category)
            )
            os.makedirs(folder_path, exist_ok=True)
            
            # Tạo tên file: brand/car_type/model/category/title.html
            filename = self._safe_filename(title) + '.html'
            filepath = os.path.join(folder_path, filename)
            
            # Lưu HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Return đường dẫn tương đối
            relative_path = os.path.relpath(filepath, '.')
            print(f"      📄 HTML: {relative_path}")
            
            # CRAWL PARTS DATA
            print(f"      🔧 Đang parse parts...")
            parts = self._parse_parts()
            print(f"      ✅ Parts: {len(parts)} items")
            
            return relative_path, parts
            
        except Exception as e:
            print(f"      ❌ Lỗi save_html: {e}")
            import traceback
            traceback.print_exc()
            return None, []
    
    def _parse_parts(self):
        """Parse parts từ trang hiện tại"""
        try:
            parts = []
            
            # Tìm bảng parts
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, ".table-bordered-1 tbody tr.part-search-tr")
                print(f"    🔍 Tìm thấy {len(rows)} rows")
            except Exception as e:
                print(f"    ⚠️  Không tìm thấy table: {e}")
                return []
            
            if not rows:
                print(f"    ⚠️  Không có rows nào!")
                return []
            
            for idx, row in enumerate(rows, 1):
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
                    else:
                        print(f"    ⚠️  Row {idx} có {len(cells)} cells (cần ít nhất 6)")
                        
                except Exception as e:
                    print(f"    ⚠️  Lỗi parse row {idx}: {e}")
                    continue
            
            return parts
            
        except Exception as e:
            print(f"    ❌ Lỗi _parse_parts: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def save_all_html_from_json(self, input_file, output_file):
        """Lưu HTML cho tất cả URLs trong JSON VÀ cập nhật cấu trúc JSON gốc"""
        
        # Load JSON data
        data = self.load_json(input_file)
        
        # Copy sang file output ngay từ đầu (để không động vào file gốc)
        if input_file != output_file:
            self.save_json(data, output_file)
            print(f"✅ Đã copy {input_file} → {output_file}")
        
        total_saved = 0
        total_failed = 0
        total_parts = 0
        
        # Loop through brands
        for brand in data:
            brand_name = brand['brand']
            print(f"\n{'='*60}")
            print(f"🏢 Brand: {brand_name}")
            print(f"{'='*60}")
            
            # Loop through car types
            for car_type_idx, car_type in enumerate(brand.get('car_types', []), 1):
                car_type_name = car_type['car_type']
                print(f"\n{'─'*60}")
                print(f"🚗 Car Type [{car_type_idx}]: {car_type_name}")
                print(f"{'─'*60}")
                
                car_type_start_time = time.time()
                
                # Loop through models
                for model_idx, model in enumerate(car_type.get('models', []), 1):
                    model_name = model['model']
                    print(f"\n  📦 Model [{model_idx}]: {model_name}")
                    
                    # SET FOLDER CHO MODEL NÀY - CHỈ 1 LẦN
                    self.set_current_model_folder(brand_name, car_type_name, model_name)
                    
                    model_start_time = time.time()
                    
                    # Loop through categories
                    for category in model.get('categories', []):
                        category_name = category['category']
                        print(f"\n    📁 Category: {category_name}")
                        print(f"    📋 Titles: {len(category.get('titles', []))}")
                        
                        # Loop through titles
                        for idx, title in enumerate(category.get('titles', []), 1):
                            title_name = title['title']
                            title_url = title['url']
                            
                            print(f"\n      [{idx}/{len(category['titles'])}] 📝 {title_name}")
                            
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
                                title['html_file'] = html_file
                                title['parts'] = parts
                                total_saved += 1
                                total_parts += len(parts)
                            else:
                                title['html_file'] = None
                                title['parts'] = []
                                total_failed += 1
                    
                    # BACKUP SAU MỖI MODEL
                    model_elapsed = time.time() - model_start_time
                    print(f"\n  ⏱️  Hoàn thành Model {model_name} trong {model_elapsed/60:.1f} phút")
                    self.save_backup(data, brand_name, car_type_idx, model_idx)
                    
                    # Lưu output file chính
                    self.save_json(data, output_file)
                
                # Tổng kết car type
                car_type_elapsed = time.time() - car_type_start_time
                print(f"\n✅ Hoàn thành Car Type {car_type_name} trong {car_type_elapsed/60:.1f} phút")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 TỔNG KẾT:")
        print(f"   ✅ HTML đã lưu: {total_saved}")
        print(f"   🔧 Parts đã crawl: {total_parts}")
        print(f"   ❌ Thất bại: {total_failed}")
        print(f"{'='*60}")
    
    def close(self):
        """Close browser"""
        self.driver.quit()


# Main execution
if __name__ == "__main__":
    saver = PartsouqHTMLSaver()
    
    try:
        # QUAN TRỌNG: Đặt tên output khác input để không ghi đè file gốc!
        input_file = "Infiniti_Complete.json"
        output_file = "Infiniti.json"  # File mới, không động file gốc
        
        print(f"📥 Input: {input_file}")
        print(f"📤 Output: {output_file}")
        print(f"💾 Backup: backups/")
        print("="*60)
        
        # Lưu HTML cho tất cả URLs
        saver.save_all_html_from_json(input_file, output_file)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
    finally:
        saver.close()