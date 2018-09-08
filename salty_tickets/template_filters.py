from salty_tickets import app


@app.template_filter('price')
def price_filter(amount: float) -> str:
    return '£{:.2f}'.format(amount)


@app.template_filter('price_int')
def price_int_filter(amount: float) -> str:
    return '£{:.0f}'.format(amount)


@app.template_filter('price_stripe')
def price_stripe_filter(amount: float) -> str:
    return '{:.0f}'.format(amount*100)
