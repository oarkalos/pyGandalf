from pyGandalf.core.base_window import BaseWindow

from pyGandalf.utilities.logger import logger

import OpenGL.GL as gl
import glfw

import platform

class OpenGLWindow(BaseWindow):
    def create(self):
        # Initialize GLFW
        if not glfw.init():
            logger.critical("GLFW could not be initialized!")
            exit(-1)

        # Set GLFW window hints
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)

        if platform.system() == "Darwin":
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE);

        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE);

        # Create a windowed mode window and its OpenGL context
        self.handle = glfw.create_window(self.width, self.height, self.title, None, None)
        if not self.handle:
            logger.critical("OpenGL Window could not be created!")
            glfw.terminate()
            exit(-1)

        # Make the window's context current
        glfw.make_context_current(self.handle)

        # Set vsync mode
        glfw.swap_interval(1 if self.vertical_sync else 0)

        # Obtain the GL versioning system info
        gVersionLabel = f'OpenGL {gl.glGetString(gl.GL_VERSION).decode()} GLSL {gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION).decode()} Renderer {gl.glGetString(gl.GL_RENDERER).decode()}'
        logger.info(gVersionLabel)

        # Attach the callbacks.
        self.set_callbacks()

    def dispatch_main_loop(self, main_loop):
        while not glfw.window_should_close(self.handle):
            glfw.poll_events()
            main_loop()
            glfw.swap_buffers(self.handle)

    def get_context(self):
        return glfw.get_current_context()