# Django Allauth Social Providers Configuration
# Place your Google and Facebook OAuth credentials here (never commit real secrets)

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': 'GOOGLE_CLIENT_ID',  # Replace with your Google client ID
            'secret': 'GOOGLE_CLIENT_SECRET',  # Replace with your Google client secret
            'key': ''
        }
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SDK_URL': 'https://connect.facebook.net/en_US/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'picture.type(large)',
        ],
        'APP': {
            'client_id': 'FACEBOOK_APP_ID',  # Replace with your Facebook App ID
            'secret': 'FACEBOOK_APP_SECRET',  # Replace with your Facebook App Secret
            'key': ''
        }
    }
}
