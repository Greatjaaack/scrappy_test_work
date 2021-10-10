import scrapy


class CatalogSpider(scrapy.Spider):
    name = 'CatalogMagnitCosmetic'
    allowed_domains = ['magnitcosmetic.ru']
    start_urls = ["https://magnitcosmetic.ru/catalog/kosmetika/makiyazh_glaz/"]
    urls = ["https://magnitcosmetic.ru/catalog/kosmetika/makiyazh_glaz/", "https://magnitcosmetic.ru/catalog/kosmetika/parfyumeriya/", "https://magnitcosmetic.ru/catalog/kosmetika/ukhod_za_volosami/", "https://magnitcosmetic.ru/catalog/kosmetika/ukhod_za_kozhey_litsa/", "https://magnitcosmetic.ru/catalog/kosmetika/ukhod_za_kozhey_tela/"]
    max_pages_count = 20
    # uagent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
    # proxy = '176.74.9.62:8080'
    custom_settings = {'FEED_URI': "MagnetCatalog.json",
                       'FEED_FORMAT': 'json'}


    def start_requests(self):
        for link in self.urls:
            for page in range(1, self.max_pages_count + 1):
                url = f'{link}?PAGEN_1={page}' # страница со следующими 12 товарами
                yield scrapy.Request(url, meta={'proxy':'http://176.74.9.62:8080'}, callback=self.parse_pages) # в meta поместил беслптный прокси москвы


    def parse_pages(self, response, **kwargs):
        #обработчик страниц c 12 товарами
        for link in response.css('.product__link::attr("href")').extract():
            url = response.urljoin(link)
            yield scrapy.Request(url, meta={'proxy':'http://176.74.9.62:8080'}, callback=self.parse)

    def parse(self, response, **kwargs):
        #обработчик страницы с 1 товаром

        #понял, что нужно отправить запрос "https://magnitcosmetic.ru/local/ajax/load_remains/catalog_load_remains.php", чтоб получить json-файл с ценой, наличием товара на остатках и т.д. но так и не понял как это сделать...

        price_data = {
            "current": 0.,  # {float} Цена со скидкой, если скидки нет то = original"
            "original": float(str(response.css(".action-card__price-rub js-item_price-value-rub::text").extract_first('').strip()) + str(response.css("action-card__price-kop js-item_price-value-kop::text").extract_first('').strip())) if response.css(".action-card__price-rub js-item_price-value-rub::text").extract_first('') else 'Price is not avalibale',
            "sale_tag": "Скидка {0}%"# {str} Если есть скидка на товар то необходимо вычислить процент скидки и записать формате: "Скидка {}%"
        }

        #stoks
        stock = {
            "in_stock": True if response.css(".js-product_quantity::text").extract() else False,
            "count": 0
        }

        #images
        assets = {
        "main_image": "https://" + self.allowed_domains[-1] + response.css(".product__image::attr('src')").extract()[0],  # {str} Ссылка на основное изображение товара
        "set_images":  ["https://" + self.allowed_domains[-1] + src for src in response.css(".product__image::attr('src')").extract()],  # {list of str} Список больших изображений товара
        "view360": [],  # {list of str}
        "video": []  # {list of str}
        }


        #description if products
        product_features = response.css(".action-card__cell::text").extract()
        metadata = {
            product_features[i].strip(":"): product_features[i+1].strip() for i in range(0, len(product_features), 2)
        }

        #final_json_file
        product_description = {
            "timestamp": "",  # Текущее время в формате timestamp
            "RPC": response.request.url.split('/')[-2],
            "url": response.request.url,
            "title": response.css(".action-card__name::text").extract_first().strip(),
            "marketing_tags": response.css(".event__product-title::text").extract(),
            "brand": metadata['Бренд'],
            "section": [i.strip() for i in response.xpath("//div[@class='breadcrumbs__item']/a/text()").getall()],
            "price_data": price_data,
            "stock": stock,
            "assets": assets,
            "metadata": metadata,
            "variants": 1
        }

        yield product_description
