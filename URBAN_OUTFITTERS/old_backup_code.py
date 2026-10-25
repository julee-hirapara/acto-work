
def extract_data(url, sel, has_key):
    hash_id = url_to_id(url)
    rows = []
    new_row = []

    try:
        # ------------------------ #
        # Parse JSON-LD
        # ------------------------ #
        blocks = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
        if not blocks:
            print("No JSON-LD block found")
            return rows

        try:
            data = json.loads(blocks[-1].strip())
        except Exception as e:
            print(f"JSON-LD parsing failed: {e}")
            return rows

        name = data.get("name")
        mpn = data.get("mpn")
        category = data.get("category", "")
        category = category.replace(" > ", "/") if category else ""

        offers_data = data.get("offers", {})
        sku_list = []

        if isinstance(offers_data, list):
            sku_list = [
                str(item.get("sku"))
                for item in offers_data
                if item.get("sku")
            ]
            price_currency = offers_data[0].get("priceCurrency", "USD")

        elif isinstance(offers_data, dict):
            price_currency = offers_data.get("priceCurrency", "USD")
        else:
            price_currency = "USD"

        # ------------------------ #
        # Parse URBN State
        # ------------------------ #
        state_block = sel.xpath('//script[@id="urbnInitialState"]/text()').get()
        if not state_block:
            print("No urbnInitialState found")
            return rows

        try:
            temp = json.loads(state_block)
            data_2 = json.loads(temp) if isinstance(temp, str) else temp
        except Exception as e:
            print(f"urbnInitialState parsing failed: {e}")
            return rows

        # Detect product key
        try:
            key_name = next(
                key for key in data_2.keys()
                if key.startswith("product--")
            )
        except StopIteration:
            print("Product key not found")
            return rows

        product_core = data_2.get(key_name, {}).get("core", {}).get("catalogData", {})
        if not product_core:
            print("catalogData missing")
            return rows

        pid = product_core.get("productId")
        rating_count = product_core.get("reviews", {}).get("count")
        average_ratings = product_core.get("reviews", {}).get("averageRating")

        product_info = product_core.get("product", {})
        long_desc = product_info.get("longDescription", "")
        brand = product_info.get("brand", "")
        brand_desc = product_info.get("brandDescription", "")

        description_parts = [long_desc]
        if brand_desc:
            description_parts.extend([brand, brand_desc])

        description = " ".join(description_parts)
        clean_description = re.sub(r"[\\\-\*]", "", description)
        clean_description = re.sub(r"\s+", " ", clean_description).strip()

        color_list = product_core.get("skuInfo", {}).get("primarySlice", {}).get("sliceItems", [])
        size_list = product_core.get("skuInfo", {}).get("secondarySlice", {}).get("sliceItems", [])
        selector_map = data_2.get(key_name, {}).get("skuSelection", {}).get("selectorMap", {})
        onsite_html_colors = sel.xpath(
            "//fieldset[@data-qa-color]//label[contains(@class, 'c-pwa-custom-radio__label')]//img/@alt").getall()
        parsed = urlparse(url)
        slug = parsed.path.split("/")[-1]

        # ------------------------ #
        # LOOP ONLY FRONTEND VISIBLE VARIANTS
        # ------------------------ #
        for selector_key, selector_value in selector_map.items():

            try:
                if not selector_value:
                    continue

                # Optional safety check
                if selector_value.get("isDisplayable") is False:
                    continue

                sku_id = str(selector_value.get("skuId"))
                if not sku_id:
                    continue

                if sku_list and sku_id not in sku_list:
                    continue

                saleprice = round(float(selector_value.get("salePrice", 0)), 2)
                listprice = round(float(selector_value.get("listPrice", 0)), 2)

                discount = listprice - saleprice
                discount = None if discount == 0 else round(discount, 2)

                stock_level = selector_value.get("stockLevel", 0)
                is_in_stock = "FALSE" if stock_level == 0 else "TRUE"

                colour_id = selector_value.get("colorId")
                size_id = selector_value.get("sizeId")

                # ---- Map Size ----
                size = None
                fit_type = None

                for size_item in size_list:
                    fit_label = size_item.get("displayName")
                    for s in size_item.get("includedSizes", []):
                        if str(s.get("id")) == str(size_id):
                            size = s.get("displayName")
                            fit_type = fit_label
                            break
                    if size:
                        break

                new_size_format = f"{size} - {fit_type}" if fit_type else size
                fit_type_param = fit_type.upper() if fit_type else ""

                # ---- Map Color ----
                colour_name = None
                image_url = ""
                alt_image_urls = ""
                color_code = None

                for color_item in color_list:
                    if str(color_item.get("code")) == str(colour_id):
                        colour_name = color_item.get("displayName")
                        color_code = color_item.get("code")
                        image_id = color_item.get("id")

                        images = [
                            f"https://images.urbndata.com/is/image/UrbanOutfitters/{image_id}_{img}?$xlarge$&fit=constrain&qlt=80&wid=640"
                            for img in color_item.get("images", [])
                        ]

                        if images:
                            image_url = images[0]
                            alt_image_urls = " | ".join(images[1:])
                        break

                size_param = urllib.parse.quote_plus(size) if size else ""

                variant_url = (
                    f"https://www.urbanoutfitters.com/shop/{slug}"
                    f"?color={color_code}&type={fit_type_param}&quantity=1&size={size_param}"
                )

                row = {
                    "website": "Urban Outfitters",
                    "pid": pid,
                    "name": name,
                    "short_description": None,
                    "description": clean_description,
                    "category": category,
                    "image_url": image_url,
                    "price": listprice,
                    "price_currency": price_currency,
                    "sale_price": saleprice,
                    "final_price": saleprice,
                    "discount": discount,
                    "is_on_sale": None,
                    "is_in_stock": is_in_stock,
                    "keywords": None,
                    "brand": brand if brand else None,
                    "manufacturer": None,
                    "mpn": mpn,
                    "upc_ean": None,
                    "sku": sku_id,
                    "colour": colour_name,
                    "gender": None,
                    "size": size,
                    "variant_price": saleprice,
                    "alternate_image_urls": alt_image_urls,
                    "link_url": variant_url,
                    "num_ratings": rating_count,
                    "avg_ratings": average_ratings,
                    "hash_id": str(hash_id),
                    "main_url": url,
                    "size_type": new_size_format,
                }

                rows.append(row)

            except Exception as variant_error:
                print(f"Variant error for {selector_key}: {variant_error}")
                continue
        if onsite_html_colors:
            print(onsite_html_colors)
            for item in rows:
                if item.get("colour") not in onsite_html_colors:
                    continue
                else:
                    new_row.append(item)
        else:
            new_row = rows
        print(new_row)
        return new_row
        # return rows

    except Exception as main_error:
        print(f"Fatal error while extracting {url}: {main_error}")
        return new_row