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

def unify_sizes(image_paths, resample_filter=Image.Resampling.LANCZOS, progress_callback=None):
    """Resizes all images to match smallest dimensions."""
    if not image_paths:
        return
    
    min_w = min(w for _, w, h in image_paths)
    min_h = min(h for _, w, h in image_paths)
    
    total = len(image_paths)
    for i, (path, w, h) in enumerate(image_paths):
        if progress_callback:
            progress_callback(i + 1, total, f"Unifying: {os.path.basename(path)}")
            
        if w == min_w and h == min_h:
            continue
            
        img = Image.open(path).convert("RGBA")
        scale = min(min_w / w, min_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        img = img.resize((new_w, new_h), resample_filter)
        
        canvas = Image.new("RGBA", (min_w, min_h), (0, 0, 0, 0))
        x_offset = (min_w - new_w) // 2
        y_offset = (min_h - new_h) // 2
        canvas.paste(img, (x_offset, y_offset))
        
        canvas.save(path, "PNG")

def split_images(input_path=".", output_dir="output", padding=10, min_size=128, unify=False, resample_filter=Image.Resampling.LANCZOS, progress_callback=None):
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
        unify_sizes(all_results, resample_filter, progress_callback)

if __name__ == "__main__":
    split_images()
