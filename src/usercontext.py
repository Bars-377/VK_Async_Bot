from typing import Dict, Any

class UserContext:
    """Единое хранилище пользовательских переменных бота.

    Все значения сгруппированы по user_id, а не лежат в общем словаре
    CtxStorage с ключами вида "<user_id>: <имя переменной>".
    Методы get/set сохраняют совместимость с существующими вызовами.
    """

    PRESERVED_KEYS = {
        "talon_select_vkontakte_reg",
        "department_select_vkontakte_reg",
        "phone",
    }

    def __init__(self) -> None:
        self._users: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _split_key(key: str) -> tuple[str, str]:
        user_id, separator, variable = str(key).partition(": ")
        if not separator or not user_id or not variable:
            raise ValueError(
                f"Некорректный ключ пользовательского контекста: {key!r}. "
                "Ожидается формат '<user_id>: <variable>'."
            )
        return user_id, variable

    def get(self, key: str, default: Any = None) -> Any:
        user_id, variable = self._split_key(key)
        return self._users.get(user_id, {}).get(variable, default)

    def set(self, key: str, value: Any) -> None:
        user_id, variable = self._split_key(key)
        self._users.setdefault(user_id, {})[variable] = value

    def reset_user(self, user_id: int | str) -> None:
        """Удаляет данные пользователя, сохраняя поля, нужные текущему сценарию."""
        user_key = str(user_id)
        user_data = self._users.get(user_key)
        if not user_data:
            return

        self._users[user_key] = {
            key: value
            for key, value in user_data.items()
            if key in self.PRESERVED_KEYS
        }
        if not self._users[user_key]:
            self._users.pop(user_key, None)
