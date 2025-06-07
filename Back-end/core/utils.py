import io, os
from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse
import qrcode
from PIL import Image
from django.utils.text import slugify
from django.core import signing


def make_table_token(table):
    payload = {
        'restaurant_id': table.map.restaurant.id,
        'table_id':      table.id,
    }
    return signing.dumps(
        payload,
        key=settings.SECRET_KEY,
        salt='table-token',
        serializer=signing.JSONSerializer
    )




def generate_table_qr(table, request):
    """
    Generates a QR for this Table instance pointing at its detail URL,
    embeds the restaurant’s icon at center, and returns path and image content.
    """
    # Build the URL dynamically using the request object
    token = make_table_token(table)
    url   = request.build_absolute_uri(
        reverse('restaurant:table', args=[token])
    )


    # Load & resize the logo
    logo_path = os.path.join(settings.MEDIA_ROOT, 'core', 'Icon.png')
    logo = Image.open(logo_path)
    qr_size = 300
    logo_size = int(qr_size * 0.2)
    logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)

    # Create QR
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)


    # Paste logo at center
    pos = ((qr_img.size[0] - logo.size[0]) // 2,
           (qr_img.size[1] - logo.size[1]) // 2)
    qr_img.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)

    # Save into a Django file
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    filename = f"qr_table_{slugify(table.name)}.png"

    rest_slug = slugify(table.map.restaurant.name)
    map_slug = slugify(table.map.name)
    path = os.path.join('qr_codes', rest_slug, map_slug, filename)

    return path, ContentFile(buffer.getvalue())