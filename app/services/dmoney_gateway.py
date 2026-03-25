"""
D-Money Payment Gateway Integration
Production URL: https://pg.d-moneyservice.dj
Handles: Token generation, PreOrder creation, and Checkout URL generation
"""

import json
import time
import base64
import secrets
import string
import logging
import urllib.parse
from typing import Dict, Optional
from datetime import datetime

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import requests
import urllib3

from app.config import settings

# Configure logging
logger = logging.getLogger("DmoneyGateway")


class DmoneyPaymentGateway:
    """D-Money Payment Gateway - Production Implementation"""

    # Fixed production endpoints
    GATEWAY_PATH          = "/apiaccess/payment/gateway"
    TOKEN_PATH            = "/payment/v1/token"
    PREORDER_PATH         = "/payment/v1/merchant/preOrder"
    DEFAULT_CHECKOUT_BASE = "https://pg.d-moneyservice.dj/payment/web/paygate"

    # All date formats the D-Money API has been observed to return
    _EXPIRY_FORMATS = [
        "%Y%m%d%H%M%S",        # 20260218211816
        "%Y-%m-%d %H:%M:%S",   # 2026-02-18 21:18:16
        "%Y-%m-%dT%H:%M:%S",   # 2026-02-18T21:18:16
        "%Y/%m/%d %H:%M:%S",   # 2026/02/18 21:18:16
    ]

    def __init__(self):
        """Initialize the gateway with credentials from settings"""

        self.base_url   = settings.DMONEY_BASE_URL.strip().rstrip("/")
        self.x_app_key  = settings.DMONEY_X_APP_KEY.strip()
        self.app_secret = settings.DMONEY_APP_SECRET.strip()
        self.verify_ssl = settings.DMONEY_VERIFY_SSL

        self.appid         = settings.DMONEY_APPID.strip()
        self.merch_code    = settings.DMONEY_MERCH_CODE.strip()
        self.business_type = settings.DMONEY_BUSINESS_TYPE.strip()
        self.notify_url    = settings.DMONEY_NOTIFY_URL.strip()
        self.redirect_url  = settings.DMONEY_REDIRECT_URL.strip()

        self.checkout_base_url = (
            settings.DMONEY_CHECKOUT_BASE_URL.strip()
            or self.DEFAULT_CHECKOUT_BASE
        )

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("⚠️  SSL verification is DISABLED")

        self._load_private_key()

        self.token: Optional[str] = None
        self.token_expiry: Optional[float] = None

        logger.info("✅ DmoneyPaymentGateway initialised")

    def _mask(self, value: str, head: int = 8, tail: int = 4) -> str:
        """Mask sensitive strings for safe display/logging."""
        if not value or len(value) <= head + tail:
            return value
        return f"{value[:head]}...{value[-tail:]}"

    def _api_url(self, path: str) -> str:
        """Build a full API URL"""
        base = self.base_url
        if self.GATEWAY_PATH in base:
            base = base[: base.index(self.GATEWAY_PATH)]

        if not path.startswith("/"):
            path = "/" + path

        url = f"{base}{self.GATEWAY_PATH}{path}"
        logger.debug(f"API URL → {url}")
        return url

    def _parse_expiry(self, expiry_str: str) -> float:
        """Parse the expirationDate returned by the API"""
        expiry_str = expiry_str.strip()
        for fmt in self._EXPIRY_FORMATS:
            try:
                return datetime.strptime(expiry_str, fmt).timestamp()
            except ValueError:
                continue

        try:
            from dateutil import parser as du_parser
            return du_parser.parse(expiry_str).timestamp()
        except Exception:
            pass

        logger.warning(
            f"⚠️  Could not parse expirationDate '{expiry_str}' — "
            "defaulting token TTL to 1 hour."
        )
        return time.time() + 3600

    def _load_private_key(self):
        """Load RSA private key from settings (base64-encoded DER)"""
        raw_b64 = settings.DMONEY_PRIVATE_KEY_B64.strip()
        if not raw_b64:
            raise ValueError("DMONEY_PRIVATE_KEY_B64 is missing from settings")

        try:
            der_bytes = base64.b64decode(raw_b64)
            self.private_key = serialization.load_der_private_key(
                der_bytes, password=None, backend=default_backend()
            )
            logger.info("🔐 RSA private key loaded successfully")
        except Exception as exc:
            raise ValueError(f"Failed to load private key: {exc}") from exc

    def _generate_order_id(self) -> str:
        ts     = datetime.now().strftime("%Y%m%d%H%M%S")
        suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"ORD{ts}{suffix}"

    def _nonce(self, length: int = 32) -> str:
        return "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length))

    def _timestamp(self) -> str:
        return str(int(time.time()))

    def _signing_string(self, params: Dict) -> str:
        """Build the canonical signing string"""
        exclude = {"sign", "sign_type", "biz_content"}
        items = sorted(
            (k, str(v))
            for k, v in params.items()
            if k not in exclude and v is not None and str(v).strip()
        )
        s = "&".join(f"{k}={v}" for k, v in items)
        logger.debug(f"Signing string: {s}")
        return s

    def _sign(self, params: Dict) -> str:
        """RSA-PSS SHA-256 signature, base64-encoded"""
        raw = self._signing_string(params)
        sig = self.private_key.sign(
            raw.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(sig).decode("utf-8")

    def _ensure_token(self):
        """Fetch a new token if none exists or the current one is about to expire"""
        buffer = 60
        if self.token and self.token_expiry and time.time() < (self.token_expiry - buffer):
            return
        self.get_token()

    def get_token(self) -> Dict:
        """Authenticate and retrieve a bearer token"""
        url = self._api_url(self.TOKEN_PATH)
        headers = {
            "Content-Type": "application/json",
            "X-APP-Key": self.x_app_key,
        }
        payload = {"appSecret": self.app_secret}

        logger.info(f"🔑 POST {url}")
        resp = requests.post(
            url, json=payload, headers=headers,
            verify=self.verify_ssl,
            timeout=settings.DMONEY_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("errorCode"):
            raise RuntimeError(f"Token error [{data['errorCode']}]: {data.get('errorMsg')}")

        self.token = data["token"]

        expiry_str = data.get("expirationDate")
        if expiry_str:
            self.token_expiry = self._parse_expiry(expiry_str)
        else:
            self.token_expiry = time.time() + 3600

        ttl = int(self.token_expiry - time.time())
        logger.info(f"✅ Token acquired — expires in {ttl}s")
        return data

    def create_preorder(
        self,
        amount: float,
        title: str,
        order_id: Optional[str] = None,
        currency: str = "DJF",
        timeout: str = "120m",
        notify_url: Optional[str] = None,
        redirect_url: Optional[str] = None,
    ) -> Dict:
        """Create a PreOrder at D-Money"""
        self._ensure_token()

        order_id     = order_id or self._generate_order_id()
        notify_url   = (notify_url   or self.notify_url).strip()
        redirect_url = (redirect_url or self.redirect_url).strip()

        if not order_id.isalnum():
            raise ValueError("order_id must be alphanumeric only")

        nonce_str = self._nonce()
        timestamp = self._timestamp()

        sign_params = {
            "appid":           self.appid,
            "business_type":   self.business_type,
            "merch_code":      self.merch_code,
            "merch_order_id":  order_id,
            "method":          "payment.preorder",
            "nonce_str":       nonce_str,
            "notify_url":      notify_url,
            "redirect_url":    redirect_url,
            "timeout_express": timeout,
            "timestamp":       timestamp,
            "title":           title,
            "total_amount":    str(int(amount)),
            "trade_type":      "Checkout",
            "trans_currency":  currency,
            "version":         "1.0",
        }
        signature = self._sign(sign_params)

        payload = {
            "nonce_str":   nonce_str,
            "method":      "payment.preorder",
            "version":     "1.0",
            "sign_type":   "SHA256WithRSA",
            "timestamp":   timestamp,
            "sign":        signature,
            "biz_content": {
                "appid":           self.appid,
                "merch_code":      self.merch_code,
                "merch_order_id":  order_id,
                "business_type":   self.business_type,
                "trade_type":      "Checkout",
                "trans_currency":  currency,
                "total_amount":    str(int(amount)),
                "timeout_express": timeout,
                "title":           title,
                "notify_url":      notify_url,
                "redirect_url":    redirect_url,
            },
        }

        url = self._api_url(self.PREORDER_PATH)
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.token,
            "X-APP-Key":     self.x_app_key,
        }

        logger.info(f"💳 POST {url}  order={order_id}  amount={int(amount)} {currency}")

        resp = requests.post(
            url, json=payload, headers=headers,
            verify=self.verify_ssl,
            timeout=settings.DMONEY_TIMEOUT_SEC,
        )

        try:
            data = resp.json()
        except Exception:
            raise RuntimeError(f"Non-JSON response ({resp.status_code}): {resp.text}")

        if resp.status_code != 200:
            raise RuntimeError(
                f"PreOrder failed [{resp.status_code}]: {data.get('errorMsg', resp.text)}"
            )

        if data.get("errorCode"):
            raise RuntimeError(
                f"PreOrder error [{data['errorCode']}]: "
                f"{data.get('errorMsg')} — {data.get('errorSolution', '')}"
            )

        logger.info("✅ PreOrder created successfully")
        return data

    def generate_checkout_url(self, prepay_id: str, language: str = "en") -> str:
        """Build the payment checkout URL"""
        nonce_str = self._nonce()
        timestamp = self._timestamp()

        sign_params = {
            "appid":      self.appid,
            "merch_code": self.merch_code,
            "nonce_str":  nonce_str,
            "prepay_id":  prepay_id,
            "timestamp":  timestamp,
        }
        signature = self._sign(sign_params)

        query_params = {
            "appid": self.appid,
            "merch_code": self.merch_code,
            "nonce_str": nonce_str,
            "prepay_id": prepay_id,
            "timestamp": timestamp,
            "sign": signature,
            "sign_type": "SHA256WithRSA",
            "version": "1.0",
            "trade_type": "Checkout",
            "language": language,
        }
        query = urllib.parse.urlencode(query_params)

        url = f"{self.checkout_base_url}?{query}"
        logger.info("✅ Checkout URL generated")
        return url

    def create_payment(
        self,
        amount: float,
        title: str,
        order_id: Optional[str] = None,
        currency: str = "DJF",
        timeout: str = "120m",
        notify_url: Optional[str] = None,
        redirect_url: Optional[str] = None,
        language: str = "en",
    ) -> Dict:
        """High-level helper: PreOrder → Checkout URL"""
        order_id = order_id or self._generate_order_id()

        raw = self.create_preorder(
            amount=amount,
            title=title,
            order_id=order_id,
            currency=currency,
            timeout=timeout,
            notify_url=notify_url,
            redirect_url=redirect_url,
        )

        biz_content = raw.get("biz_content")
        if isinstance(biz_content, str):
            try:
                biz = json.loads(biz_content)
            except Exception:
                biz = {}
        elif isinstance(biz_content, dict):
            biz = biz_content
        else:
            biz = {}

        prepay_id = biz.get("prepay_id")
        checkout_url = self.generate_checkout_url(prepay_id, language) if prepay_id else None

        return {
            "success":      True,
            "order_id":     order_id,
            "prepay_id":    prepay_id,
            "checkout_url": checkout_url,
            "amount":       amount,
            "currency":     currency,
            "raw_response": raw,
        }
