# Static Images Directory

This directory contains static images for the CMS Desa application.

## Required Images:

### Logo and Branding
- `logo.png` - Main logo for the village website (recommended: 200x80px)
- `logo-white.png` - White version of logo for dark backgrounds
- `favicon.ico` - Website favicon (16x16px, 32x32px)

### Default Images
- `default-avatar.png` - Default user avatar (150x150px)
- `default-cover.jpg` - Default cover image for content without images (800x400px)
- `placeholder.jpg` - General placeholder image (600x400px)

### Hero Images
- `hero-bg.jpg` - Hero section background image (1920x1080px)
- `village-hall.jpg` - Village hall image for about page (800x600px)

## Image Guidelines:

### File Formats
- Use PNG for logos and images with transparency
- Use JPG for photographs and complex images
- Use WebP for better compression (with fallbacks)

### Size Recommendations
- Logo: Maximum 200px width, optimized for web
- Cover images: 800x400px (2:1 ratio)
- Avatar images: 150x150px (square)
- Hero images: 1920x1080px (16:9 ratio)

### Optimization
- Compress images for web use
- Use appropriate quality settings (80-90% for JPG)
- Consider using responsive images with multiple sizes

## Usage in Templates:

```html
<!-- Logo -->
<img src="{{ url_for('static', filename='images/logo.png') }}" alt="Logo Desa">

<!-- Default avatar -->
<img src="{{ url_for('static', filename='images/default-avatar.png') }}" alt="Avatar">

<!-- Cover image with fallback -->
{% if content.cover_image %}
    <img src="{{ url_for('static', filename='uploads/' + content.cover_image) }}" alt="{{ content.title }}">
{% else %}
    <img src="{{ url_for('static', filename='images/default-cover.jpg') }}" alt="Default Cover">
{% endif %}
```

## Notes:
- All images should be optimized for web delivery
- Consider using a CDN for better performance in production
- Implement lazy loading for better page load times
- Provide alt text for accessibility