import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

class PartsouqCrawler:
    def __init__(self):
        # Setup undetected Chrome để bypass Cloudflare
        options = uc.ChromeOptions()
        # options.add_argument('--headless=new')  # Uncomment để chạy ngầm
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = uc.Chrome(options=options, version_main=None)
        self.base_url = "https://partsouq.com"
        
    def get_all_brands(self):
        """Crawl all brand links from homepage"""
        print("🔍 Đang crawl danh sách brands...")
        
        try:
            self.driver.get(self.base_url)
            
            # Chờ Cloudflare check xong
            print("⏳ Đang chờ Cloudflare check... (có thể mất 5-10s)")
            time.sleep(8)
            
            # Wait for brand container
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.ID, "make-icons")))
            
            # Find all brand links
            brand_elements = self.driver.find_elements(By.CSS_SELECTOR, "#make-icons .item a")
            
            brands = []
            for element in brand_elements:
                try:
                    brand_name = element.find_element(By.CLASS_NAME, "shop-title").text
                    brand_href = element.get_attribute("href")
                    
                    brands.append({
                        "brand": brand_name,
                        "href": brand_href
                    })
                    
                    print(f"✅ Found: {brand_name} - {brand_href}")
                    
                except Exception as e:
                    print(f"⚠️ Lỗi khi parse brand: {e}")
                    continue
            
            return brands
            
        except Exception as e:
            print(f"❌ Lỗi khi crawl brands: {e}")
            return []
    
    def get_car_types(self, brand_url):
        """Get all car types/models for a brand"""
        print(f"\n🚗 Đang crawl car types từ: {brand_url}")
        
        try:
            self.driver.get(brand_url)
            
            # Chờ Cloudflare check
            print("  ⏳ Đang chờ Cloudflare...")
            time.sleep(6)
            
            # Wait for panel to load
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".panel-heading")))
            
            car_types = []
            seen_urls = set()
            
            # Tìm tất cả links có href chứa '/catalog/genuine/pick'
            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/catalog/genuine/pick']")
            
            print(f"  🔍 Tìm thấy {len(all_links)} links...")
            
            for link in all_links:
                try:
                    car_type = link.text.strip()
                    car_href = link.get_attribute("href")
                    
                    if car_type and car_href and car_href not in seen_urls:
                        car_type = car_type.replace('\n', ' ').strip()
                        
                        car_types.append({
                            "car_type": car_type,
                            "href": car_href
                        })
                        
                        seen_urls.add(car_href)
                        print(f"  ✅ {car_type}")
                        
                except Exception as e:
                    continue
            
            return car_types
            
        except Exception as e:
            print(f"  ❌ Lỗi khi crawl car types: {e}")
            try:
                self.driver.save_screenshot("error_screenshot.png")
                print("  📸 Đã lưu screenshot lỗi: error_screenshot.png")
            except:
                pass
            return []
    
    def get_models(self, car_type_url):
        """Get all models for a car type"""
        print(f"\n    🔧 Đang crawl models từ: {car_type_url}")
        
        try:
            self.driver.get(car_type_url)
            
            # Chờ Cloudflare
            print("      ⏳ Đang chờ Cloudflare...")
            time.sleep(5)
            
            # Wait for table to load
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".search-result-vin")))
            
            models = []
            seen_urls = set()
            
            # Tìm tất cả rows trong table (bỏ qua header row)
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".search-result-vin tbody tr:not(:first-child)")
            
            print(f"      🔍 Tìm thấy {len(rows)} models...")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 5:
                        name = cells[0].text.strip()
                        description = cells[1].text.strip()
                        model = cells[2].text.strip()
                        options = cells[3].text.strip()
                        prod_period = cells[4].text.strip()
                        
                        # Lấy URL từ Model column
                        model_link = cells[2].find_element(By.TAG_NAME, "a")
                        model_url = model_link.get_attribute("href")
                        
                        if model and model_url and model_url not in seen_urls:
                            models.append({
                                "name": name,
                                "description": description,
                                "model": model,
                                "options": options,
                                "prod_period": prod_period,
                                "url": model_url
                            })
                            
                            seen_urls.add(model_url)
                            print(f"      ✅ {model} - {description}")
                            
                except Exception as e:
                    print(f"      ⚠️ Lỗi parse row: {e}")
                    continue
            
            return models
            
        except Exception as e:
            print(f"      ❌ Lỗi khi crawl models: {e}")
            try:
                self.driver.save_screenshot("error_models.png")
                print("      📸 Đã lưu screenshot: error_models.png")
            except:
                pass
            return []
    
    def get_categories_and_titles(self, model_url):
        """Get all categories and their titles/diagrams"""
        print(f"\n      🗂️  Đang crawl categories từ: {model_url}")
        
        try:
            self.driver.get(model_url)
            
            # Chờ Cloudflare
            print("        ⏳ Đang chờ Cloudflare...")
            time.sleep(5)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".vehicle-tg")))
            
            categories = []
            
            # BƯỚC 1: Crawl DEFAULT CATEGORY (Engine/Fuel/Tool) - đang hiển thị
            try:
                default_category_name = self.driver.find_element(By.CSS_SELECTOR, "h2.current-category").text.strip()
                default_category_name = default_category_name.replace(" Diagrams", "").strip()
                
                print(f"        📁 Default Category: {default_category_name}")
                
                # Crawl titles đang hiển thị
                default_titles = self.get_titles_only()
                
                categories.append({
                    "category": default_category_name,
                    "url": model_url,
                    "titles": default_titles
                })
                
                print(f"            ✅ {len(default_titles)} titles found")
                
            except Exception as e:
                print(f"        ⚠️ Không crawl được default category: {e}")
            
            # BƯỚC 2: Thu thập danh sách CHILD CATEGORIES
            category_info_list = []
            seen_urls = set()
            
            category_rows = self.driver.find_elements(By.CSS_SELECTOR, ".vehicle-tg tbody tr")
            print(f"        🔍 Tìm thấy {len(category_rows)} rows trong sidebar")
            
            for idx, row in enumerate(category_rows):
                try:
                    # Kiểm tra xem row này có link không
                    links = row.find_elements(By.TAG_NAME, "a")
                    
                    if links:
                        # Row có link - đây là category có thể click
                        link = links[0]
                        category_name = link.text.strip()
                        category_url = link.get_attribute("href")
                        
                        if category_name and category_url and category_url not in seen_urls:
                            category_info_list.append({
                                "name": category_name,
                                "url": category_url
                            })
                            seen_urls.add(category_url)
                            print(f"        ✅ Found Category: {category_name}")
                    else:
                        # Row không có link - parent category
                        try:
                            cell_text = row.find_element(By.TAG_NAME, "td").text.strip()
                            if cell_text:
                                print(f"        📂 Parent: {cell_text}")
                        except:
                            pass
                        
                except Exception as e:
                    print(f"        ⚠️ Lỗi parse row {idx}: {e}")
                    continue
            
            print(f"        ✅ Tổng số child categories: {len(category_info_list)}")
            
            # BƯỚC 3: Crawl titles cho từng child category
            for idx, cat_info in enumerate(category_info_list, 1):
                print(f"\n        [{idx}/{len(category_info_list)}] 📁 Crawling: {cat_info['name']}")
                
                # Navigate to category
                self.driver.get(cat_info['url'])
                time.sleep(4)
                
                # Get titles (không lấy parts)
                titles = self.get_titles_only()
                
                categories.append({
                    "category": cat_info['name'],
                    "url": cat_info['url'],
                    "titles": titles
                })
                
                print(f"            ✅ {len(titles)} titles found")
            
            return categories
        
        except Exception as e:
            print(f"      ❌ Lỗi khi crawl categories: {e}")
            try:
                self.driver.save_screenshot("error_categories.png")
                print("      📸 Đã lưu screenshot: error_categories.png")
            except:
                pass
            return []
        
    def get_titles_only(self):
        """Get all titles from current page WITHOUT crawling parts"""
        try:
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail")))
            
            titles = []
            seen_urls = set()
            
            # Find all diagram thumbnails
            thumbnails = self.driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
            
            print(f"            🔍 Tìm thấy {len(thumbnails)} thumbnails")
            
            for thumb in thumbnails:
                try:
                    # Get title from caption h5 > a
                    caption = thumb.find_element(By.CSS_SELECTOR, ".caption h5 a")
                    title_text = caption.text.strip()
                    title_url = caption.get_attribute("href")
                    
                    if title_text and title_url and title_url not in seen_urls:
                        titles.append({
                            "title": title_text,
                            "url": title_url
                        })
                        
                        seen_urls.add(title_url)
                        print(f"            ⚙️  {title_text}")
                        
                except Exception as e:
                    continue
            
            return titles
            
        except Exception as e:
            print(f"          ❌ Lỗi khi crawl titles: {e}")
            return []
    
    def save_to_json(self, data, filename="Infiniti_title.json"):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Đã lưu vào file: {filename}")
    
    def close(self):
        """Close browser"""
        self.driver.quit()


# Main execution - CRAWL 1 BRAND (TẤT CẢ TITLES)
if __name__ == "__main__":
    crawler = PartsouqCrawler()
    
    # ⚙️ CẤU HÌNH: Chọn brand cần crawl
    TARGET_BRAND = "Infiniti"  # Đổi tên brand ở đây
    
    try:
        print("="*80)
        print(f"🚀 BẮT ĐẦU CRAWL BRAND: {TARGET_BRAND} - TẤT CẢ TITLES")
        print("="*80)
        
        # Step 1: Get all brands
        brands = crawler.get_all_brands()
        print(f"\n📊 Tổng số brands: {len(brands)}")
        
        # Step 2: Tìm brand cần crawl
        target_brand_data = None
        for brand in brands:
            if brand['brand'].lower() == TARGET_BRAND.lower():
                target_brand_data = brand
                break
        
        if not target_brand_data:
            print(f"\n❌ Không tìm thấy brand: {TARGET_BRAND}")
            print(f"📋 Danh sách brands có sẵn:")
            for b in brands:
                print(f"   - {b['brand']}")
        else:
            print(f"\n✅ Tìm thấy brand: {target_brand_data['brand']}")
            print(f"🔗 URL: {target_brand_data['href']}")
            
            # Step 3: Crawl TẤT CẢ car types
            car_types = crawler.get_car_types(target_brand_data['href'])
            target_brand_data['car_types'] = []
            
            if not car_types:
                print(f"\n⚠️ Không tìm thấy car types cho {TARGET_BRAND}")
                crawler.save_to_json([target_brand_data], f"{TARGET_BRAND}_Complete.json")
            else:
                print(f"\n📦 Tìm thấy {len(car_types)} car types")
                
                # Crawl từng car type
                for ct_idx, car_type in enumerate(car_types, 1):
                    print(f"\n{'='*60}")
                    print(f"📦 [{ct_idx}/{len(car_types)}] Car Type: {car_type['car_type']}")
                    print(f"{'='*60}")
                    
                    try:
                        # Get models
                        models = crawler.get_models(car_type['href'])
                        
                        car_type_data = {
                            "car_type": car_type['car_type'],
                            "href": car_type['href'],
                            "models": []
                        }
                        
                        if not models:
                            print(f"  ⚠️ Không tìm thấy models")
                            target_brand_data['car_types'].append(car_type_data)
                            continue
                        
                        print(f"  🚙 Tìm thấy {len(models)} models")
                        
                        # Crawl TẤT CẢ models
                        for model_idx, model in enumerate(models, 1):
                            print(f"\n  🚙 [{model_idx}/{len(models)}] Model: {model['model']}")
                            
                            try:
                                # Get TẤT CẢ categories và titles
                                categories = crawler.get_categories_and_titles(model['url'])
                                
                                model_data = {
                                    "name": model['name'],
                                    "description": model['description'],
                                    "model": model['model'],
                                    "options": model['options'],
                                    "prod_period": model['prod_period'],
                                    "url": model['url'],
                                    "categories": categories
                                }
                                
                                car_type_data['models'].append(model_data)
                                
                                # Thống kê
                                total_titles = sum(len(cat['titles']) for cat in categories)
                                print(f"    ✅ {len(categories)} categories, {total_titles} titles")
                                
                            except Exception as e:
                                print(f"    ❌ Lỗi crawl model {model['model']}: {e}")
                                continue
                        
                        target_brand_data['car_types'].append(car_type_data)
                        
                        # Backup sau mỗi car type
                        crawler.save_to_json([target_brand_data], f"{TARGET_BRAND}_Progress_CT{ct_idx}.json")
                        print(f"\n  💾 Backup: {TARGET_BRAND}_Progress_CT{ct_idx}.json")
                        
                    except Exception as e:
                        print(f"  ❌ Lỗi crawl car type: {e}")
                        continue
                
                # Save final result
                crawler.save_to_json([target_brand_data], f"{TARGET_BRAND}_Complete.json")
                
                # Thống kê tổng kết
                total_car_types = len(target_brand_data['car_types'])
                total_models = sum(len(ct['models']) for ct in target_brand_data['car_types'])
                total_categories = sum(
                    len(model['categories']) 
                    for ct in target_brand_data['car_types'] 
                    for model in ct['models']
                )
                total_titles = sum(
                    len(cat['titles'])
                    for ct in target_brand_data['car_types']
                    for model in ct['models']
                    for cat in model['categories']
                )
                
                print(f"\n{'='*80}")
                print(f"✅ HOÀN THÀNH CRAWL: {TARGET_BRAND}")
                print(f"{'='*80}")
                print(f"📂 File: {TARGET_BRAND}_Complete.json")
                print(f"📊 Thống kê:")
                print(f"   - Car Types: {total_car_types}")
                print(f"   - Models: {total_models}")
                print(f"   - Categories: {total_categories}")
                print(f"   - Titles: {total_titles}")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🔒 Đóng browser...")
        crawler.close()
    
    print("\n✨ HOÀN THÀNH!")