"""
mcode-web-deploy: Direct Web Deploy Tool (Zero-LLM / Zero-Token)
Deploy static websites to MiniMax space CDN directly via backend API.
"""

__version__ = "0.1.0"

from .deployer import deploy, DeployResult, DeployError, load_access_token

__all__ = ["deploy", "DeployResult", "DeployError", "load_access_token", "__version__"]
