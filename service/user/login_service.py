class LoginService:
    """
    LoginService 用于处理登录相关逻辑
    """

    @classmethod
    def get_current_user(cls):
        """
        获取当前登录人信息。
        目前没有设计用户功能，使用 mock 假数据。
        """
        return {
            "creator_id": 1,
            "create_name": "张三",
            "org_id": 1
        }