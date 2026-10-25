"""Single source of truth for the application's user-visible identity.

Every place that shows the application name, the developer, the version or the
contact number reads it from here so the values can never drift apart again.

The application name is deliberately **not** translated: it is the product's
brand and must read "MS Media Player" in every language, exactly as the user
requested.
"""

# Product name - never translated, never localised.
APP_NAME = "MS Media Player"

APP_VERSION = "1.0.0"

# Organisation used by QSettings / platformdirs.
ORG_NAME = "MSMediaPlayer"

# Developer credit.
DEVELOPER = "محمد مسعد"
DEVELOPER_LATIN = "Mohamed Mosad"

# Contact number in international (E.164) form, without the leading "+".
# The Egyptian mobile 01040243045 becomes +20 10 40 24 30 45.
CONTACT_NUMBER = "201040243045"
# Human readable, spaced form used in the About dialog and the EULA.
CONTACT_NUMBER_DISPLAY = "+20 10 40 24 30 45"

# HTTP user agent used for network streams.
USER_AGENT = f"{APP_NAME}/{APP_VERSION}"
