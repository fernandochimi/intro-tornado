# coding: utf-8
import os.path

from uuid import uuid4

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket


class ShoppingCart(object):
    totalInventory = 10
    callbacks = []
    carts = {}

    def register(self, callback):
        self.callbacks.append(callback)

    def unregister(self, callback):
        self.callbacks.remove(callback)

    def moveItemToCart(self, session):
        if session in self.carts:
            return
        self.carts[session] = True
        self.notifyCallbacks()

    def removeItemFromCart(self, session):
        if session not in self.carts:
            return
        del(self.carts[session])
        self.notifyCallbacks()

    def notifyCallbacks(self):
        for callback in self.callbacks:
            callback(self.getInventoryCount())

    def getInventoryCount(self):
        return self.totalInventory - len(self.carts)


class DetailHandler(tornado.web.RequestHandler):
    def get(self):
        session = uuid4()
        count = self.application.ShoppingCart.getInventoryCount()
        self.render("index_new.html", session=session, count=count)


class CartHandler(tornado.web.RequestHandler):
    def post(self):
        action = self.get_argument("action")
        session = self.get_argument("session")

        if not session:
            self.set_status(400)
            return

        if action == "add":
            self.application.ShoppingCart.moveItemToCart(session)
        elif action == "remove":
            self.application.ShoppingCart.removeItemFromCart(session)
        else:
            self.set_status(400)


class StatusHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.application.ShoppingCart.register(
            self.callback)

    def on_close(self):
        self.application.ShoppingCart.unregister(
            self.callback)

    def on_message(self, message):
        pass

    def callback(self, count):
        self.write_message('{"inventoryCount": "%d"}' % count)


class Application(tornado.web.Application):
    def __init__(self):
        self.ShoppingCart = ShoppingCart()

        handlers = [
            (r"/", DetailHandler),
            (r"/cart", CartHandler),
            (r"/cart/status", StatusHandler),
        ]

        settings = {
            "template_path":
                os.path.join(os.path.dirname(__file__), "templates"),
            "static_path":
                os.path.join(os.path.dirname(__file__), "static"),
        }

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = Application()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
