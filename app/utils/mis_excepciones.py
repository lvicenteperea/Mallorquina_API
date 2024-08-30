class MadreException(Exception):

    """Excepción base para todos los errores específicos de la aplicación."""
    def __init__(self, detail, status_code: int = 500):

        self.status_code = status_code

        if isinstance(detail, dict):
            self.mi_mensaje = detail
        else:
            self.mi_mensaje = {"ret_code": -1,
                               "ret_txt": detail,
                              }
        print("Madre / Excptn: ", self.mi_mensaje, self.status_code)
        super().__init__(self.mi_mensaje['ret_txt'])

    def to_dict(self):
        return {"error": self.mi_mensaje, "status_code": self.status_code}
