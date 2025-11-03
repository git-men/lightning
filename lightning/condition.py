class Condition(dict):
    pass


class ValueCondition(Condition):
    operator = '='

    def __init__(self, field, value):
        super().__init__(self, field=field, operator=self.operator, value=value)


class ValueEqualsCondition(ValueCondition):
    pass


class ValueNotEqualsCondition(ValueCondition):
    operator = '!='


class ValueContainCondition(ValueCondition):
    operator = 'icontains'


class ValueInCondition(ValueCondition):
    operator = 'in'


class VariableCondition(Condition):
    operator = '='

    def __init__(self, field, variable):
        super().__init__(self, field=field, operator=self.operator, variable=variable)


class VariableEqualsCondition(VariableCondition):
    pass


class VariableNotEqualsCondition(VariableCondition):
    operator = '!='


class OrCondition(Condition):
    def __init__(self, *children):
        super().__init__(self, operator='OR', children=list(children))


class AndCondition(Condition):
    def __init__(self, *children):
        super().__init__(self, operator='AND', children=list(children))
