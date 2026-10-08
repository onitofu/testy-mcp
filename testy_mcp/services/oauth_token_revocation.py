from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save


class OAuthTokenRevocation:
    """Revoke OAuth credentials when an active user is deactivated."""

    @classmethod
    def connect(cls):
        pre_save.connect(
            cls._before_user_save,
            sender=settings.AUTH_USER_MODEL,
            dispatch_uid="testy_mcp.oauth_token_revocation.before_user_save",
            weak=False,
        )
        post_save.connect(
            cls._after_user_save,
            sender=settings.AUTH_USER_MODEL,
            dispatch_uid="testy_mcp.oauth_token_revocation.after_user_save",
            weak=False,
        )

    @staticmethod
    def _before_user_save(
        sender, instance, raw=False, using="default", update_fields=None, **kwargs
    ):
        instance._mcp_deactivating = False
        if (
            raw
            or instance.pk is None
            or (update_fields is not None and "is_active" not in update_fields)
            or instance.is_active
        ):
            return
        instance._mcp_deactivating = (
            sender._default_manager.using(using).filter(pk=instance.pk, is_active=True).exists()
        )

    @classmethod
    def _after_user_save(
        cls, sender, instance, raw=False, created=False, using="default", **kwargs
    ):
        deactivating = instance.__dict__.pop("_mcp_deactivating", False)
        if raw or created or not deactivating or instance.is_active:
            return
        cls.revoke_user(instance.pk, using)

    @staticmethod
    def revoke_user(user_id, using="default"):
        from oauth2_provider.models import (
            get_access_token_model,
            get_grant_model,
            get_refresh_token_model,
        )

        with transaction.atomic(using=using):
            get_refresh_token_model().objects.using(using).filter(user_id=user_id).delete()
            get_access_token_model().objects.using(using).filter(user_id=user_id).delete()
            get_grant_model().objects.using(using).filter(user_id=user_id).delete()
