from PIL import Image
import numpy as np
from scipy import ndimage
import os
import glob

def process_file(file_path, output_dir="output", padding=10, min_size=128):
    """
    Processes a single image file: detects regions and saves them.
    Returns list of (output_path, width, height) tuples.
    """
    filename = os.path.basename(file_path)
    
    try:
        img = Image.open(file_path).convert("RGBA")
    except Exception as e:
        return []

    img_array = np.array(img)
    alpha = img_array[:, :, 3]
    binary_mask = alpha > 0
    labeled_array, num_features = ndimage.label(binary_mask)
    
    results = []
    for region_id in range(1, num_features + 1):
        region_mask = labeled_array == region_id
        rows = np.any(region_mask, axis=1)
        cols = np.any(region_mask, axis=0)
        
        if not rows.any() or not cols.any():
            continue
            
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        
        w = x_max - x_min + 1
        h = y_max - y_min + 1
        
        if w <= min_size and h <= min_size:
            continue
        
        crop_array = img_array[y_min:y_max+1, x_min:x_max+1].copy()
        region_crop_mask = region_mask[y_min:y_max+1, x_min:x_max+1]
        crop_array[~region_crop_mask] = [0, 0, 0, 0]
        
        if padding > 0:
            padded = np.zeros((h + 2*padding, w + 2*padding, 4), dtype=np.uint8)
            padded[padding:padding+h, padding:padding+w] = crop_array
            crop_array = padded
        
        result = Image.fromarray(crop_array, mode="RGBA")
        
        name_part, ext_part = os.path.splitext(filename)
        output_filename = f"{name_part}_{region_id:03d}{ext_part}"
        output_path = os.path.join(output_dir, output_filename)
        
        result.save(output_path, "PNG")
        results.append((output_path, result.width, result.height))
        
    return results

def unify_sizes(image_paths, resample_filter=Image.Resampling.LANCZOS, mode="smaller", progress_callback=None):
    """Resizes all images based on the selected mode."""
    if not image_paths:
        return
    
    # 1. Collect dimensions
    dims = [(w, h) for _, w, h in image_paths]
    min_w = min(w for w, h in dims)
    min_h = min(h for w, h in dims)
    
    # 2. Determine Target Canvas Size
    target_w, target_h = min_w, min_h # Default for 'smaller'
    
    if mode == "width":
        target_w = min_w
        # Max height needed after scaling all images to target_w
        max_scaled_h = 0
        for w, h in dims:
            scale = target_w / w
            scaled_h = int(h * scale)
            if scaled_h > max_scaled_h:
                max_scaled_h = scaled_h
        target_h = max_scaled_h
        
    elif mode == "height":
        target_h = min_h
        # Max width needed after scaling all images to target_h
        max_scaled_w = 0
        for w, h in dims:
            scale = target_h / h
            scaled_w = int(w * scale)
            if scaled_w > max_scaled_w:
                max_scaled_w = scaled_w
        target_w = max_scaled_w

    # 3. Process Images
    total = len(image_paths)
    for i, (path, w, h) in enumerate(image_paths):
        if progress_callback:
            progress_callback(i + 1, total, f"Unifying: {os.path.basename(path)}")
            
        # Calculate new size for this specific image
        new_w, new_h = w, h
        
        if mode == "width":
            scale = target_w / w
            new_w = int(w * scale)
            new_h = int(h * scale)
        elif mode == "height":
            scale = target_h / h
            new_w = int(w * scale)
            new_h = int(h * scale)
        else: # smaller (default)
             scale = min(target_w / w, target_h / h)
             new_w = int(w * scale)
             new_h = int(h * scale)

        # Skip if already perfect (rare with padding logic change, but okay for exact matches)
        # Note: checking just w/h might skip padding, so we check new_w/h against target
        if new_w == target_w and new_h == target_h and w == new_w and h == new_h:
             continue
        
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize((new_w, new_h), resample_filter)
            
            canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            canvas.paste(img, (x_offset, y_offset))
            
            canvas.save(path, "PNG")
        except Exception as e:
            print(f"Error unifying {path}: {e}")


def split_images(input_path=".", output_dir="output", padding=10, min_size=128, unify=False, resample_filter=Image.Resampling.LANCZOS, unify_mode="smaller", progress_callback=None):
    """Splits transparent images."""
    os.makedirs(output_dir, exist_ok=True)
    
    png_files = []
    
    if isinstance(input_path, list):
        png_files = input_path
    elif os.path.isdir(input_path):
        png_files = glob.glob(os.path.join(input_path, "*.png"))
    else:
        if os.path.exists(input_path) and input_path.lower().endswith('.png'):
            png_files = [input_path]
    
    if not png_files:
        return

    all_results = []
    total = len(png_files)
    
    for i, file_path in enumerate(png_files):
        if progress_callback:
            progress_callback(i + 1, total, f"Processing: {os.path.basename(file_path)}")
        all_results.extend(process_file(file_path, output_dir, padding, min_size))

    if unify and all_results:
        unify_sizes(all_results, resample_filter, unify_mode, progress_callback)

if __name__ == "__main__":
    split_images()
