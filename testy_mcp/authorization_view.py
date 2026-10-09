from django.utils.translation import get_language
from oauth2_provider.views import AuthorizationView


class McpAuthorizationView(AuthorizationView):
    template_name = "testy_mcp/authorize.html"
    translations = {
        "en": {
            "title": "Allow access to TestY",
            "heading": "Allow “{application}” access to TestY?",
            "intro": "This application requests access with the parameters listed below.",
            "intro_read": "The application will be able to view TestY data.",
            "intro_write": "The application will be able to create, edit and delete TestY data.",
            "intro_read_write": (
                "The application will be able to view, create, edit and delete TestY data."
            ),
            "application": "Application",
            "account": "Your account",
            "permissions": "Requested permissions",
            "read_title": "View projects and results",
            "read_description": "View projects, test cases, test plans and results.",
            "write_title": "Create, edit and delete data",
            "write_description": (
                "Create and edit TestY data, including deleting test cases and test suites."
            ),
            "additional": "Additional authorization parameters",
            "connect": "Allow access",
            "cancel": "Cancel",
            "error_title": "Unable to connect the application",
            "error_description": "Return to your MCP client and start the connection again.",
            "fallback_application": "MCP client",
        },
        "ru": {
            "title": "Доступ к TestY",
            "heading": "Разрешить «{application}» доступ к TestY?",
            "intro": "Приложение запрашивает доступ с указанными ниже параметрами.",
            "intro_read": "Приложение сможет просматривать данные TestY.",
            "intro_write": "Приложение сможет создавать, изменять и удалять данные TestY.",
            "intro_read_write": (
                "Приложение сможет просматривать, создавать, изменять и удалять данные TestY."
            ),
            "application": "Приложение",
            "account": "Ваша учётная запись",
            "permissions": "Запрашиваемые разрешения",
            "read_title": "Просмотр проектов и результатов",
            "read_description": "Просматривать проекты, кейсы, планы и результаты.",
            "write_title": "Создание, изменение и удаление данных",
            "write_description": (
                "Создавать и изменять данные TestY, в том числе удалять кейсы и наборы тестов."
            ),
            "additional": "Дополнительные параметры авторизации",
            "connect": "Разрешить доступ",
            "cancel": "Отмена",
            "error_title": "Не удалось подключить приложение",
            "error_description": "Вернитесь в MCP-клиент и начните подключение заново.",
            "fallback_application": "MCP-клиент",
        },
    }

    def render_to_response(self, context, **response_kwargs):
        context = context.copy()
        language = "ru" if (get_language() or "").split("-")[0] == "ru" else "en"
        text = self.translations[language]
        scopes = context.get("scopes", [])
        requested_scopes = set(scopes)
        operations = [
            operation
            for operation in ("read", "write")
            if requested_scopes & {operation, f"mcp:{operation}"}
        ]
        permissions = []
        for operation in operations:
            permissions.append(
                {
                    "title": text[f"{operation}_title"],
                    "description": text[f"{operation}_description"],
                }
            )
        application = context.get("application")
        application_name = getattr(application, "name", "") or text["fallback_application"]
        context.update(
            {
                "language": language,
                "text": text,
                "application_name": application_name,
                "heading": text["heading"].format(application=application_name),
                "intro": text[f"intro_{'_'.join(operations)}"] if operations else text["intro"],
                "account_name": self.request.user.get_username(),
                "permissions": permissions,
                "additional_scopes": list(
                    dict.fromkeys(
                        scope
                        for scope in scopes
                        if scope not in {"read", "write", "mcp:read", "mcp:write"}
                    )
                ),
            }
        )
        return super().render_to_response(context, **response_kwargs)
