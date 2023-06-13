from app import App
from util import gc_collect

app = App()

app.go()
app.wait_for_ready()

gc_collect()

