from sunpy.visualization.animator import ImageAnimator


class ImageAnimatorPSI(ImageAnimator):
    """
    This is the same as `sunpy.visualization.animator.ImageAnimator`, but
    with support for custom Matplotlib axes projections.
    """
    def __init__(self, *args, projection=None, **kwargs):
        self.projection = projection
        super().__init__(*args, **kwargs)

    def _setup_main_axes(self):
        if self.axes is None:
            self.axes = self.fig.add_subplot(111, projection=self.projection)
