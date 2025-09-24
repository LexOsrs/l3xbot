from PIL import Image
from invocations import InvocationInfo

def generate_image(filename: str, invos: list[InvocationInfo]) -> None:
    base = Image.open('images/invo_off.png').convert("RGBA")
    highlighted = Image.open('images/invo_on.png').convert("RGBA")
    print(base, highlighted)

    box_width = base.width / 4
    box_height = base.height / 11

    print(box_width, box_height)

    frame = base.copy()

    for invo in invos:
        box = (
            int(invo.x * box_width),
            int(invo.y * box_height),
            int((invo.x + 1) * box_width),
            int((invo.y + 1) * box_height),
        )

        icon = highlighted.crop(box)

        position = (int(invo.x * box_width), int(invo.y * box_height))
        frame.paste(icon, position)

    frame.save(filename)
