from woe.models.core import User
from woe.views.dashboard import broadcast

l = User.objects[0]
z = User.objects[1]

broadcast(
    to=[z,],
    category="mention",
    url="/",
    title="You were mentioned in a profile comment.",
    description="",
    content=l,
    author=l
)