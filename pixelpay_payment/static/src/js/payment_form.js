/* global PixelpayCheckout */
odoo.define('payment_adyen.payment_form', require => {
    'use strict';

    const core = require('web.core');
    const ajax = require('web.ajax');

    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');

    const _t = core._t;

    const pixelMixin = {

        /**
         * Return all relevant inline form inputs based on the payment method type of the acquirer.
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @return {Object} - An object mapping the name of inline form inputs to their DOM element
         */
        _getInlineFormInputs: function (acquirerId) {
            if (this.pixelInfo.acquirerInfo.payment_method_type === "credit_card") {
                return {
                    holder: document.getElementById(`o_pixel_holder_name_${acquirerId}`),
                    card: document.getElementById(`o_pixel_card_${acquirerId}`),
                    month: document.getElementById(`o_pixel_month_${acquirerId}`),
                    year: document.getElementById(`o_pixel_year_${acquirerId}`),
                    code: document.getElementById(`o_pixel_code_${acquirerId}`),
                    saveToken: document.getElementById(`o_payment_save_as_token`),
                };
            } else {
                return {
                    accountName: document.getElementById(`o_pixel_account_name_${acquirerId}`),
                    accountNumber: document.getElementById(
                        `o_pixel_account_number_${acquirerId}`
                    ),
                    abaNumber: document.getElementById(`o_pixel_aba_number_${acquirerId}`),
                    accountType: document.getElementById(`o_pixel_account_type_${acquirerId}`),
                };
            }
        },

        /**
         * Return the credit card or bank data to pass to the Accept.dispatch request.
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @return {Object} - Data to pass to the Accept.dispatch request
         */
        _getPaymentDetails: function (acquirerId) {
            const inputs = this._getInlineFormInputs(acquirerId);
            if (this.pixelInfo.acquirerInfo.payment_method_type === 'credit_card') {
                return {
                    cardData: {
                        holderName: inputs.holder.value,
                        cardNumber: inputs.card.value.replace(/ /g, ''), // Remove all spaces
                        month: inputs.month.value,
                        year: inputs.year.value,
                        cardCode: inputs.code.value,
                        saveToken: inputs.saveToken && inputs.saveToken.checked
                    },
                };
            } else {
                return {
                    bankData: {
                        nameOnAccount: inputs.accountName.value.substring(0, 22), // Max allowed by acceptjs
                        accountNumber: inputs.accountNumber.value,
                        routingNumber: inputs.abaNumber.value,
                        accountType: inputs.accountType.value,
                    },
                };
            }
        },

        _prepareInlineForm: function (provider, paymentOptionId, flow) {
            if (provider !== 'pixel') {
                return this._super(...arguments);
            }

            let acceptJSUrl = 'https://unpkg.com/@pixelpay/sdk-core';

            return this._getPaymentData(paymentOptionId, flow).then(data => {
                const pixelInfo = {
                    acquirerInfo: data[0],
                    orderInfo: data[1]
                }
                if (data.length == 3) {
                    _.extend(pixelInfo.orderInfo, data[2])
                }

                this.pixelInfo = pixelInfo;
                if (flow !== 'token') {
                    this._setPaymentFlow('direct');
                }
            }).then(async () => {
                var pixelsdk = await ajax.loadJS(acceptJSUrl);
            }).guardedCatch((error) => {
                error.event.preventDefault();
                this._displayError(
                    _t("Server Error"),
                    _t("An error occurred when displayed this payment form."),
                    error.message.data.message
                );
            });
        },

        _getPaymentData: async function (paymentOptionId, flow) {
            this.pixelToken = false
            if (flow === 'token') {
                var paymentInfo = await this._getPixelToken(paymentOptionId)
                paymentOptionId = paymentInfo.acquirer_id
                this.pixelToken = paymentInfo.pixelToken
            }

            var acquirerInfo = this._rpc({
                route: '/payment/pixelpay/get_acquirer_info',
                params: {
                    'acquirer_id': paymentOptionId,
                },
            })

            var partnerInfo = this._rpc({
                route: '/payment/pixelpay/get_customer_info',
                params: {
                    'partner_id': this.txContext.partnerId,
                },
            })

            var order_id = null
            if (this.txContext.transactionRoute.split('/')['1'] == 'shop') {
                order_id = parseInt(this.txContext.transactionRoute.split('/')['4'])
            } else if (this.txContext.transactionRoute.split('/')['1'] == 'my') {
                order_id = parseInt(this.txContext.transactionRoute.split('/')['3'])
            } else if (this.txContext.transactionRoute.split('/')['1'] == 'invoice') {
                order_id = parseInt(this.txContext.transactionRoute.split('/')['3'])
            } else {
                order_id = null
            }

            if (order_id != null && (this.txContext.transactionRoute.split('/')['1'] == 'shop' || this.txContext.transactionRoute.split('/')['1'] == 'my')) {
                var saleOrderInfo = this._rpc({
                    route: '/payment/pixelpay/get_order_info',
                    params: {
                        'order_id': order_id,
                    },
                })
                return Promise.all([acquirerInfo, partnerInfo, saleOrderInfo])
            } else if (order_id != null && this.txContext.transactionRoute.split('/')['1'] == 'invoice') {
                var saleOrderInfo = this._rpc({
                    route: '/payment/pixelpay/get_invoice_info',
                    params: {
                        'invoice_id': order_id,
                    },
                })
                return Promise.all([acquirerInfo, partnerInfo, saleOrderInfo])
            }

            return Promise.all([acquirerInfo, partnerInfo])
        },

        _getToken: async function (secureData, acquirerId) {
            await this._generatePixelToken(secureData).then(response => {
                if (response.errors || response.success === false) {
                    let error = response.message;
                    this._displayError(
                        _t("Server Error"),
                        _t("We are not able to process your payment."),
                        error
                    );
//                    return false
                    return Promise.reject(new Error(error));
                }

                const token = response.data.token
                var encryptedAESToken = CryptoJS.AES.encrypt(token, this.pixelInfo.acquirerInfo.pixel_secret_key).toString();
                this.pixelToken = encryptedAESToken
                var token_id = false
                return token_id = this._rpc({
                    route: '/payment/pixel/create_token',
                    params: {
                        'acquirer_id': acquirerId,
                        'partner_id': parseInt(this.txContext.partnerId),
                        'pixel_token': encryptedAESToken,
                        'mask': response.data.mask,
                        'network': response.data.network
                    },
                })
            })
        },


        /**
         * Simulate a feedback from a payment provider and redirect the customer to the status page.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} provider - The provider of the acquirer
         * @param {number} acquirerId - The id of the acquirer handling the transaction
         * @param {object} processingValues - The processing values of the transaction
         * @return {Promise}
         */
        _processDirectPayment: async function (provider, acquirerId, processingValues) {
            if (provider !== 'pixel') {
                return this._super(...arguments);
            }

            if (!this._validateFormInputs(acquirerId)) {
                this._enableButton(); // The submit button is disabled at this point, enable it
                $('body').unblock(); // The page is blocked at this point, unblock it
                return Promise.resolve();
            }

            // Build the authentication and card data objects to be dispatched to Pixelpay
            const secureData = {
                authData: {
                    endpoint: this.pixelInfo.acquirerInfo.pixel_endpoint,       //endpoint: "https://{endpoint}")
                    key: this.pixelInfo.acquirerInfo.pixel_key,                //key: "2222222222"
                    hash: this.pixelInfo.acquirerInfo.pixel_secret_key,         //hash: "elhashmd5delsecretkeydelcomercio"
                },
                ...this._getPaymentDetails(acquirerId),
            };

            const save = secureData.cardData.saveToken

//            if (save === null){
            if (this.txContext.landingRoute === '/my/payment_method'){
                await this._getToken(secureData, acquirerId).then(tokenId => {
                    return Promise.resolve().then(() => window.location = 'payment_method');
                }, error => {
                    return false
                    })
            } else if (save === true){
                await this._getToken(secureData, acquirerId).then(tokenId => {
                    return this._processTokenPayment(provider, tokenId, processingValues);
                }, error => {
                    return false
                    })
            } else {
                await this._directPayment(secureData).then(response => {
                const data = {
                    payment_transaction: response.data,
                    errors: response.errors,
                    success: response.success,
                    message: response.message
                    }
                return this._responseHandler(data, processingValues)
                })
            }
        },

        /**
         * Redirect the customer to the status route.
         *
         * For an acquirer to redefine the processing of the payment by token flow, it must override
         * this method.
         *
         * @private
         * @param {string} provider - The provider of the token's acquirer
         * @param {number} tokenId - The id of the token handling the transaction
         * @param {object} processingValues - The processing values of the transaction
         * @return {undefined}
         */
        _processTokenPayment: async function (provider, tokenId, processingValues) {
            if (provider !== 'pixel') {
                return this._super(...arguments);
            }
            // The flow is already completed as payments by tokens are immediately processed
            await this._payWithToken(this.pixelToken).then(response => {
                const data = {
                    token_id: tokenId,
                    payment_transaction: response.data,
                    errors: response.errors,
                    success: response.success,
                    message: response.message
                    }
                return this._responseHandler(data, processingValues, tokenId)
            })
        },

        _getPixelToken: function (tokenId) {
            return this._rpc({
                route: '/payment/pixel/get_token',
                params: {
                    'tokenId': tokenId,
                },
            })
        },

        /**
         * Handle the response from PixelPay and initiate the payment.
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @param {object} response - The payment nonce returned by PixelPay
         * @return {Promise}
         */
        _responseHandler: function (data, processingValues, paymentOptionId = false ) {
            if (data.errors || data.success === false) {
                let error = data.message;
                this._displayError(
                    _t("Server Error"),
                    _t("We are not able to process your payment."),
                    error
                );
                return Promise.resolve();
            }
            // Create the transaction and retrieve the processing values
            _.extend(data, processingValues);
            // Initiate the payment
            return this._rpc({
                route: '/payment/pixel/payment',
                params: {
                    'data': data,
                }
            }).then(() => window.location = '/payment/status').guardedCatch((error) => {
                error.event.preventDefault();
                this._displayError(
                    _t("Server Error"),
                    _t("We are not able to process your payment."),
                    error.message.data.message
                );
            });
        },


        /**
         * Checks that all payment inputs adhere to the DOM validation constraints.
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @return {boolean} - Whether all elements pass the validation constraints
         */
        _validateFormInputs: function (acquirerId) {
            const inputs = Object.values(this._getInlineFormInputs(acquirerId));
//            return inputs.every(element => element.reportValidity());
            return true
        },

        _generatePixelToken: async function (secureData) {
            var self = this;
            const settings = new Models.Settings()
            const card = new Models.Card();
            const billing = new Models.Billing();
            const card_token = new Requests.CardTokenization();

            if (this.pixelInfo.acquirerInfo.state === 'enabled') {
                settings.setupEndpoint(this.pixelInfo.acquirerInfo.pixel_endpoint)                                                  // https://pixel-pay.com
                settings.setupCredentials(this.pixelInfo.acquirerInfo.pixel_key, this.pixelInfo.acquirerInfo.pixel_secret_key);     // "BG1519245341", "3bf20bf9d4ae9756532d9ec2d13849b1"
            } else {
                settings.setupSandbox()
            }

            card.number = secureData.cardData.cardNumber
            card.cvv2 = secureData.cardData.cardCode
            card.expire_month = secureData.cardData.month
            card.expire_year = '20' + secureData.cardData.year
            card.cardholder = secureData.cardData.holderName

           // const billing = new Billing()
            billing.address = this.pixelInfo.orderInfo.partnerInfo.billing_address//"Ave Circunvalacion"
            billing.country = this.pixelInfo.orderInfo.partnerInfo.billing_country//"HN"
            billing.state = this.pixelInfo.orderInfo.partnerInfo.billing_state//"HN-CR"
            billing.city = this.pixelInfo.orderInfo.partnerInfo.billing_city//"San Pedro Sula"
            billing.phone = this.pixelInfo.orderInfo.partnerInfo.billing_phone//"99999999"
            billing.zip = this.pixelInfo.orderInfo.partnerInfo.billing_zip

            card_token.setCard(card);
            card_token.setBilling(billing);

            const tokenization = new Services.Tokenization(settings);
            // with async / await
            try {
                const response = await tokenization.vaultCard(card_token)
                return {'self': self, 'errors': response.errors, 'data': response.data, 'message': response.message, 'success': response.success}
            } catch (error) {
            // ERROR
            }
        },

        _payWithToken: async function(token) {
            var decryptedBytesToken = CryptoJS.AES.decrypt(token, this.pixelInfo.acquirerInfo.pixel_secret_key);
            var plainTextToken = decryptedBytesToken.toString(CryptoJS.enc.Utf8);
            var self = this;

            const settings = new Models.Settings()
            const item = new Models.Item();
            const order = new Models.Order();
            const sale = new Requests.SaleTransaction();

            if (this.pixelInfo.acquirerInfo.state === 'enabled') {
                settings.setupEndpoint(this.pixelInfo.acquirerInfo.pixel_endpoint)                                                  // https://pixel-pay.com
                settings.setupCredentials(this.pixelInfo.acquirerInfo.pixel_key, this.pixelInfo.acquirerInfo.pixel_secret_key);     // "BG1519245341", "3bf20bf9d4ae9756532d9ec2d13849b1"
            } else {
                settings.setupSandbox()
            }

            // Se instancia el servicio de Transaction
            const service = new Services.Transaction(settings)

            // Creación del objeto Order
            order.id = this.pixelInfo.orderInfo.saleOrderInfo.order_name // 'TEST-1234'
            order.currency = this.pixelInfo.orderInfo.saleOrderInfo.order_currency // 'HNL'
            order.amount = this.pixelInfo.orderInfo.saleOrderInfo.order_amount // 1
            order.customer_name = this.pixelInfo.orderInfo.saleOrderInfo.order_customer_name //'Jhon Doe'
            order.customer_email = this.pixelInfo.orderInfo.partnerInfo.email //'jhondow@pixel.hn'

            // Se instancia el request de SaleTransaction que es el que realiza la transaccion
            sale.setOrder(order)

            // Aqui se setea el token de la tarjeta, no es necesario enviar el objeto card ni el obejeto billing
            sale.setCardToken(plainTextToken)

            // Se realiza la transacción don el método doSale
            try {
                var response = await service.doSale(sale)
                return {'self': self, 'errors': response.errors, 'data': response.data, 'message': response.message, 'success': response.success}
            } catch (error) {
            // ERROR
            }
        },

        _directPayment: async function (secureData) {
            var self = this;
            const settings = new Models.Settings()
            const order = new Models.Order()
            const card = new Models.Card();
            const billing = new Models.Billing();
            const sale = new Requests.SaleTransaction();

            if (this.pixelInfo.acquirerInfo.state === 'enabled') {
                settings.setupEndpoint(this.pixelInfo.acquirerInfo.pixel_endpoint)
                settings.setupCredentials(this.pixelInfo.acquirerInfo.pixel_key, this.pixelInfo.acquirerInfo.pixel_secret_key);
            } else {
                settings.setupSandbox()
            }

            const service = new Services.Transaction(settings)

            // Creación del objeto Order
            order.id = this.pixelInfo.orderInfo.saleOrderInfo.order_name // 'TEST-1234'
            order.currency = this.pixelInfo.orderInfo.saleOrderInfo.order_currency // 'HNL' 
            order.amount = this.pixelInfo.orderInfo.saleOrderInfo.order_amount // 1
            order.customer_name = this.pixelInfo.orderInfo.saleOrderInfo.order_customer_name // 'Jhon Doe'
            order.customer_email = this.pixelInfo.orderInfo.partnerInfo.email //'jhondow@pixel.hn'

            card.number = secureData.cardData.cardNumber
            card.cvv2 = secureData.cardData.cardCode
            card.expire_month = secureData.cardData.month
            card.expire_year = '20' + secureData.cardData.year
            card.cardholder = this.pixelInfo.orderInfo.partnerInfo.partner

           // const billing = new Billing()
            billing.address = this.pixelInfo.orderInfo.partnerInfo.billing_address//"Ave Circunvalacion"
            billing.country = this.pixelInfo.orderInfo.partnerInfo.billing_country//"HN"
            billing.state = this.pixelInfo.orderInfo.partnerInfo.billing_state//"HN-CR"
            billing.city = this.pixelInfo.orderInfo.partnerInfo.billing_city//"San Pedro Sula"
            billing.phone = this.pixelInfo.orderInfo.partnerInfo.billing_phone//"99999999"
            billing.zip = this.pixelInfo.orderInfo.partnerInfo.billing_zip

            // Se instancia el request de SaleTransaction que es el que realiza la transaccion
            sale.setCard(card)
            sale.setBilling(billing)
            sale.setOrder(order)

            try {
                const response = await service.doSale(sale)
                return {'self': self, 'errors': response.errors, 'data': response.data, 'message': response.message, 'success': response.success}
            } catch (error) {
                // ERROR
            }
        },

    };

    checkoutForm.include(pixelMixin);
    manageForm.include(pixelMixin);
});
