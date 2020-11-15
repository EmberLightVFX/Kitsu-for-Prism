import os
import sys

modulePath = os.path.join(
    os.path.abspath(os.path.dirname(
        os.path.dirname(__file__))), "external_modules"
)
sys.path.append(modulePath)

sys.path.append(os.path.join(os.path.dirname(__file__), "UserInterfaces"))
sys.path.append(os.path.dirname(__file__))
