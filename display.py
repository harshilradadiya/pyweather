import pygame
import os
import time
from system_data import SystemData
from settings import ICON_BASE_DIR, ICON_DICTIONARY, ICON_TYPES, COMPASS_DIR

DEFAULT_DRIVERS = ('fbcon', 'directfb', 'svgalib', 'Quartz')
DEFAULT_SIZE = (1024, 600)
DEFAULT_SCREEN = 'full_screen'


class DisplayDriver:

    def __init__(self, drivers=DEFAULT_DRIVERS, size=DEFAULT_SIZE, screen_type=DEFAULT_SCREEN, borders=(5, 5),
                 border_width=3, line_color=(255, 255, 255), font='freesans', font_color=(255, 255, 255),
                 icons=ICON_DICTIONARY):
        """DisplayDriver class is the class that build the base display for use in the weather
        app.  Argument descriptions: drivers is a tuple of strings with available SDL_VIDEODRIVER
        environmental varaibles; size is a tuple of two integers describing the x, y size of the
        screen; screen_type is a string value that corresponds to the pygame constants for
        dispay.set_mode
        """

        formats = {'no_frame': pygame.NOFRAME, 'full_screen': pygame.FULLSCREEN, 'double_buff': pygame.DOUBLEBUF,
                   'hw_surface': pygame.HWSURFACE, 'open_GL': pygame.OPENGL, 'resizable': pygame.RESIZABLE}

        self._system_data = SystemData()
        self._display_instance = None
        self._drivers = drivers
        self._size = size
        self._borders = borders
        self._border_width = border_width
        self._line_color = line_color
        self._font = font
        self._font_color = font_color
        self._format = formats[screen_type]
        self._icons = icons
        self._base_dir = os.getcwd() + ICON_BASE_DIR
        self._scale_icons = True
        self._xmax = self._size[0] - self._borders[0]
        self._ymax = self._size[1] - self._borders[1]
        self._av = 1
        self._av_time = 1
        self._screen = None
        self._blits = []

    def __append_blits(self, blits):

        for blit in blits:
            self._blits.append(blit)

    def __get_driver(self):
        has_driver = False
        for driver in self._drivers:
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print('Driver: {} not loaded.'.format(driver))
                continue
            print('Driver: {} used.'.format(driver))
            has_driver = True
            break

        if not has_driver:
            raise AssertionError('No video driver available for use!')

    def __render_screen(self):
        for _ in range(len(self._blits)):
            blit = self._blits.pop() # pop off each item once drawn to allow for updates to display
            self._screen.blit(blit[0], blit[1])

    def __draw_screen(self):
        """This function is intended to be used by the display_start function.
        It attempts to build the blank screen and raises an error if it fails."""

        self._screen = pygame.display.set_mode(self._size, self._format)

        if not self._screen:
            raise AssertionError('Screen not defined')

        self._screen.fill((0, 0, 0))
        pygame.font.init()

        # Mouse hider -- Comment the next line to see mouse over the display
        pygame.mouse.set_visible(0)
        pygame.display.update()

    def __draw_frames(self):
        """This function should be called by the display_start function only. It renders the frames for the display"""
        xmin = self._borders[0]
        ymin = self._borders[1]
        xmax = self._xmax
        ymax = self._ymax
        line_width = self._border_width

        # Horizontal line settings
        hz = (0.1, 0.5, 0.58)

        # Vertical line settings
        vt = (0.33, 0.66, 0.2, 0.4, 0.6, 0.8)

        self._screen.fill((0, 0, 0))

        # Draw Screen Border
        pygame.draw.line(self._screen, self._line_color, (xmin, xmin), (xmax, xmin), line_width)  # Top
        pygame.draw.line(self._screen, self._line_color, (xmin, xmin), (xmin, ymax), line_width)  # Left
        pygame.draw.line(self._screen, self._line_color, (xmin, ymax), (xmax, ymax), line_width)  # Bottom
        pygame.draw.line(self._screen, self._line_color, (xmax, ymin), (xmax, ymax), line_width)  # Right Edge

        # Draw Inner Frames
        # Horizontal lines (1, 2, 3)
        for h in hz:
            pygame.draw.line(self._screen, self._line_color, (xmin, ymax * h), (xmax, ymax * h), line_width)

        # Vertical lines (1, 2)
        for j in range(2):
            v = vt[j]
            pygame.draw.line(self._screen, self._line_color, (xmax * v, ymax * hz[2]),
                             (xmax * v, ymax * hz[0]), line_width)

        # Vertical lines (3 - 6)
        for j in range(2, len(vt)):
            v = vt[j]
            pygame.draw.line(self._screen, self._line_color, (xmax * v, ymax), (xmax * v, ymax * hz[2]), line_width)

    def __display_datetime(self):

        th = 0.07     # Time Text Height
        sh = 0.03     # Seconds Text Height
        dh = 0.06     # Date Text Height
        dt_y = 13     # Date Y Position
        tm_y = 10     # Time Y Position
        tm_y_sm = 15  # Time Y Position Small

        tfont = pygame.font.SysFont(self._font, int(self._ymax * th), bold=1)  # Time Font
        dfont = pygame.font.SysFont(self._font, int(self._ymax * dh), bold=1)  # Date Font
        sfont = pygame.font.SysFont(self._font, int(self._ymax * sh), bold=1)  # Small Font for Seconds

        tm1 = time.strftime("%H:%M", time.localtime())  # Time String
        tm2 = time.strftime("%S", time.localtime())     # Seconds String
        dt1 = time.strftime("%d %b %y").upper()         # Date String

        # Build the Date / Time
        rtm1 = tfont.render(tm1, True, self._font_color)
        (tx1, ty1) = rtm1.get_size()
        rtm2 = sfont.render(tm2, True, self._font_color)
        (tx2, ty2) = rtm2.get_size()
        rdt1 = dfont.render(dt1, True, self._font_color)
        (dx1, dy1) = rdt1.get_size()

        tp = self._xmax / 2 - (tx1 + tx2) / 2
        dp = self._xmax - (dx1 + (self._borders[1] * 2))
        self._screen.blit(rtm1, (tp, tm_y))
        self._screen.blit(rtm2, (tp + tx1 + 3, tm_y_sm))
        self._screen.blit(rdt1, (dp, dt_y))

    def __get_signal_icon(self):
        sig_no = self._system_data.ws.sig_strength
        return self._base_dir + self._icons['sig{}'.format(sig_no)]

    def __display_connected(self):
        xmin = self._borders[0]
        ymin = self._borders[1]
        station_scale = 0.35
        signal_scale = 0.25

        station_icon = pygame.image.load_extended(self._base_dir + self._icons['weather_station']).convert_alpha()
        signal_icon = pygame.image.load_extended(self.__get_signal_icon()).convert_alpha()
        (stix, stiy) = station_icon.get_size()
        (sgix, sgiy) = signal_icon.get_size()

        if self._scale_icons:
            station_icon = pygame.transform.scale(station_icon, (int(stix * station_scale), int(stiy * station_scale)))
            (stix, stiy) = station_icon.get_size()
            signal_icon = pygame.transform.scale(signal_icon, (int(sgix * signal_scale), int(sgiy * signal_scale)))

        self._screen.blit(station_icon, (xmin * 2, ymin))
        self._screen.blit(signal_icon, (stix + 14, ymin + 9))

    def __display_forecasts(self):
        # TODO: Maybe I'll add some form of (3, 5, 7) day forecast option
        days = 5

        # TODO: make this part of self
        hz = (0.1, 0.5, 0.58)
        vt = (0.33, 0.66, 0.2, 0.4, 0.6, 0.8)

        vdiff = vt[4] - vt[3]
        yo = self._ymax * hz[2] + 5
        vc = 0 + vdiff / 2  # Y center

        th = 0.045          # Text Height
        rpth = 0.08         # Rain Present Text Height
        gp = 5              # Line Spacing Gap

        font = pygame.font.SysFont(self._font, int(self._ymax * th), bold=1)
        lgfont = pygame.font.SysFont(self._font, int(self._ymax * rpth), bold=1)

        for j in range(days):
            vci = vc + (j * vdiff)
            today = self._system_data.forecasts.forecasts[j]
            header = font.render(today.day, True, self._line_color)
            temps = font.render(today.high_temp + ' / ' + today.low_temp, True, self._line_color)
            rain = lgfont.render(today.rain + '%', True, self._line_color)

            icon_path = self._base_dir + 'forecast/unknown.png'
            if today.icon in self._system_data.weather_icons:
                icon_path = self._base_dir + self._system_data.weather_icons[today.icon]
            else:
                print(today.icon + ' unknown')

            icon = pygame.image.load_extended(icon_path)

            (hx, hy) = header.get_size()
            (tx, ty) = temps.get_size()
            (rx, ry) = rain.get_size()
            (ix, iy) = icon.get_size()

            """
            if self._scale_icons:
                icon = pygame.transform.scale(icon, (int(ix * 1.15), int(iy * 1.15)))
                (ix, iy) = icon.get_size()
            """
            if iy < 104:
                ye = (104 - iy) / 2
            else:
                ye = 0

            self._screen.blit(header, (self._xmax * vci - hx / 2, yo))
            self._screen.blit(icon, (self._xmax * vci - ix / 2, hy + yo + ye + (gp * 2)))
            self._screen.blit(temps, (self._xmax * vci - tx / 2, self._ymax - (ry + ty + (gp * 2))))
            self._screen.blit(rain, (self._xmax * vci - rx / 2, self._ymax - (ry + gp)))

    def __weather_vane(self):

        yc = ((self._ymax * .5 - self._ymax * .1) / 2) + (self._ymax * .1)
        vc = 0.5 * self._xmax
        th = 0.1
        smth = 0.04

        lgfont = pygame.font.SysFont(self._font, int(self._ymax * th), bold=1)
        font = pygame.font.SysFont(self._font, int(self._ymax * smth), bold=1)

        mph = font.render('mph', True, self._line_color)
        speed = lgfont.render(self._system_data.ws.wind_speed['current'], True, self._line_color)
        try:
            wd = self._system_data.wind_dirs[self._system_data.ws.wind_direction]
            wf = self._system_data.ws.wind_power
        except KeyError:
            wd = 'unknown'
            wf = '1'

        icon = pygame.image.load_extended(self._base_dir +
                                          'compass/{}_{}.png'.format(wd, wf)).convert_alpha()

        (ix, iy) = icon.get_size()
        (sx, sy) = speed.get_size()
        (mx, my) = mph.get_size()

        self._screen.blit(speed, (vc - sx / 2, yc - sy / 2))
        self._screen.blit(icon, (vc - ix / 2, yc - iy / 2))
        self._screen.blit(mph, (vc - mx / 2, yc + (sy / 2) - (my / 2)))

    def __display_indoor(self):
        offset = self._ymax * .09
        yb = self._ymax * 0.58
        yt = self._ymax * 0.5
        xc = (self._xmax * 0.33) / 2
        xl = self._borders[0]
        xr = self._xmax * 0.33
        th = 0.045
        smth = 0.03

        font = pygame.font.SysFont(self._font, int(self._ymax * smth), bold=1)
        lgfont = pygame.font.SysFont(self._font, int(self._ymax * th), bold=1)

        name = font.render('Indoor', True, self._line_color)
        temp = lgfont.render('{} f'.format(self._system_data.indoor.temp_f + chr(0x00B0)), True, self._line_color)
        humid = lgfont.render('{}% RH'.format(self._system_data.indoor.humidity), True, self._line_color)

        (nx, ny) = name.get_size()
        (tx, ty) = temp.get_size()
        (hx, hy) = humid.get_size()

        self._screen.blit(name, (xc - nx / 2, yt))
        self._screen.blit(temp, (xl + offset, yb - ty))
        self._screen.blit(humid, (xr - hx - offset, yb - hy))

    def __display_feels_like(self):
        data = self._system_data.ws
        centering = self._xmax * .085
        yb = self._ymax * 0.58
        yt = self._ymax * 0.5
        xl = self._xmax * 0.66
        xr = self._xmax
        lc = xl + centering
        rc = xr - centering
        th = 0.045
        smth = 0.03

        font = pygame.font.SysFont(self._font, int(self._ymax * smth), bold=1)
        lgfont = pygame.font.SysFont(self._font, int(self._ymax * th), bold=1)

        def add_symbol(val):
            if val != 'NA':
                val += chr(0x00B0) + " f"
                return val
            return val

        heat_idx_label = font.render('Heat Index', True, self._line_color)
        heat_idx = lgfont.render('{}'.format(add_symbol(data.heat_index)), True, self._line_color)
        wind_chill_label = font.render('Wind Chill', True, self._line_color)
        wind_chill = lgfont.render('{}'.format(add_symbol(data.wind_chill)), True, self._line_color)

        (hlx, hly) = heat_idx_label.get_size()
        (hix, hiy) = heat_idx.get_size()
        (wclx, wcly) = wind_chill_label.get_size()
        (wcx, wcy) = wind_chill.get_size()

        self._screen.blit(heat_idx_label, (lc - hlx / 2, yt))
        self._screen.blit(heat_idx, (lc - hix / 2, yb - hiy))
        self._screen.blit(wind_chill_label, (rc - wclx / 2, yt))
        self._screen.blit(wind_chill, (rc - wcx / 2, yb - wcy))

    def __display_left_frame(self):
        # TODO: Clean up variables
        data = self._system_data.ws

        centering = self._xmax * .085

        # yb = self._ymax * 0.5
        yt = self._ymax * 0.1
        offset = self._ymax * .04
        text_border = self._ymax * .008
        xc = (self._xmax * 0.33) / 2
        yc = ((self._ymax * .5 - self._ymax * .1) / 2) + (self._ymax * .1)
        xl = self._borders[0]
        xr = self._xmax * 0.33
        lc = xl + centering
        rc = xr - centering
        smth = 0.034
        lth = 0.085
        th = 0.055

        font = pygame.font.SysFont(self._font, int(self._ymax * th), bold=1)
        smfont = pygame.font.SysFont(self._font, int(self._ymax * smth), bold=1)
        lgfont = pygame.font.SysFont(self._font, int(self._ymax * lth), bold=1)

        # TODO: Remove the random generator and fill with sensor data
        temp_label = smfont.render('Temp({})'.format('f'), True, self._line_color)
        temp = lgfont.render(data.temp['current'], True, self._line_color)
        var = lgfont.render(data.humidity['current'], True, self._line_color)
        var_label = smfont.render('Humidity(RH)', True, self._line_color)
        up = pygame.image.load_extended(self._base_dir + 'navigation/up_arrow.png')
        down = pygame.image.load_extended(self._base_dir + 'navigation/down_arrow.png')

        (tx, ty) = temp.get_size()
        (tlx, tly) = temp_label.get_size()
        (vx, vy) = var.get_size()
        (vlx, vly) = var_label.get_size()
        (ux, uy) = up.get_size()
        (dx, dy) = down.get_size()

        # add render items to the blit list
        blits = [(temp_label, (lc - tlx / 2, yc - (ty / 2) - (tly / 2) - text_border)),
                 (temp, (lc - tx / 2, yc - ty / 2)),
                 (var_label, (rc - vlx / 2, yc - (vy / 2) - (vly / 2) - text_border)),
                 (var, (rc - vx / 2, yc - vy / 2)),
                 (up, (rc - ux / 2, yc - (vy / 2) - vly - uy + text_border)),
                 (down, (rc - dx / 2, yc + (vy / 2) + text_border))
                 ]

        self.__append_blits(blits)

    def __display_wind_avg(self):
        centering = self._xmax * .085
        offset = self._ymax * .008
        yb = self._ymax * 0.58
        yt = self._ymax * 0.5
        xl = self._xmax * 0.33
        xr = self._xmax * 0.66
        lc = xl + centering
        rc = xr - centering
        lth = 0.045
        th = 0.03
        smth = .025

        smfont = pygame.font.SysFont(self._font, int(self._ymax * smth), bold=1)
        font = pygame.font.SysFont(self._font, int(self._ymax * th), bold=1)
        lgfont = pygame.font.SysFont(self._font, int(self._ymax * lth), bold=1)

        wind_peak_label = font.render('Wind Gust', True, self._line_color)
        peak_wind = lgfont.render(self._system_data.ws.wind_gust, True, self._line_color)
        wind_avg_label = font.render('Avg. Wind', True, self._line_color)
        wind_avg = lgfont.render(self._system_data.ws.wind_avg, True, self._line_color)
        mph = smfont.render('mph', True, self._line_color)

        (wplx, wply) = wind_peak_label.get_size()
        (wpx, wpy) = peak_wind.get_size()
        (walx, waly) = wind_avg_label.get_size()
        (wax, way) = wind_avg.get_size()
        (mx, my) = mph.get_size()

        self._screen.blit(wind_peak_label, (lc - wplx / 2, yt))
        self._screen.blit(peak_wind, (lc - wpx / 2, yb - wpy))
        self._screen.blit(wind_avg_label, (rc - walx / 2, yt))
        self._screen.blit(wind_avg, (rc - wax / 2, yb - way))
        self._screen.blit(mph, (lc + (wpx / 2) + offset, yb - wpy))
        self._screen.blit(mph, (rc + (wax / 2) + offset, yb - way))

    def __display_sensor_detail_data(self):

        data = self._system_data.ws
        c = 'current'
        h = ['hour', 'day', 'week', 'month', 'year']
        rv = h[0]

        offset = self._ymax * .022
        bo = offset * 2
        text_border = self._ymax * .004
        centerline = self._xmax * .088
        r_offset = self._xmax * .055

        # Size and position variables
        yb = self._ymax * 0.5
        yt = self._ymax * 0.1
        xc = (self._xmax * 0.33) / 2 + (self._xmax * 0.66)
        xl = self._xmax * 0.66
        xr = self._xmax
        lc = xl + centerline * 2
        rc = xr - r_offset
        smth = 0.024
        lth = 0.035
        th = 0.031

        # Todo: Make this part of self or store it in settings
        hist_view = ['Peak', 'Average']
        hist_view_time = ['Hour', 'Day', 'Week', 'Month', 'Year']
        cf = ['c', 'f']

        font = pygame.font.SysFont(self._font, int(self._ymax * th), bold=1)
        smfont = pygame.font.SysFont(self._font, int(self._ymax * smth), bold=1)
        lgfont = pygame.font.SysFont(self._font, int(self._ymax * lth), bold=1)

        # Render labels
        curr = lgfont.render('Current', True, self._line_color)
        hist = lgfont.render(hist_view[1], True, self._line_color)
        hist_time = smfont.render(hist_view_time[0], True, self._line_color)
        trend = smfont.render('Trend', True, self._line_color)
        temp_label = font.render('Temp ({}):'.format(cf[1]), True, self._line_color)
        c_temp = font.render(data.temp[c] + chr(0x00B0), True, self._line_color)
        h_temp = font.render(data.temp[rv] + chr(0x00B0), True, self._line_color)
        humid_label = font.render('Humidity (RH):', True, self._line_color)
        c_humid = font.render(data.humidity[c], True, self._line_color)
        h_humid = font.render(data.humidity[rv] + '%', True, self._line_color)
        baro_label = font.render('Pressure (inHg)', True, self._line_color)
        c_baro = font.render(data.baro[c], True, self._line_color)
        h_baro = font.render(data.baro[rv], True, self._line_color)
        wind_label = font.render('Speed (mph)', True, self._line_color)
        c_wind_speed = font.render(data.wind_speed[c], True, self._line_color)
        h_wind_speed = font.render(data.wind_speed[rv], True, self._line_color)
        wind_dir_label = font.render('Direction', True, self._line_color)
        c_wind_direction = font.render(data.wind_direction_deg[c] + chr(0x00B0), True, self._line_color)
        h_wind_direction = font.render(data.wind_direction_deg[rv] + chr(0x00B0), True, self._line_color)
        li_label = font.render('Lumens', True, self._line_color)
        c_lumen = font.render(data.lumen, True, self._line_color)
        h_lumen = font.render('N/A', True, self._line_color)

        # Draw header
        (cx, cy) = curr.get_size()
        (hx, hy) = hist.get_size()
        self._screen.blit(curr, (lc - cx / 2, yt + offset))
        self._screen.blit(hist, (rc - hx / 2, yt + offset))

        # Draw sub-header
        (htx, hty) = hist_time.get_size()
        (tx, ty) = trend.get_size()
        self._screen.blit(hist_time, (rc - htx / 2, yt + cy + offset))
        # self._screen.blit(trend, (((rc - xc) / 2) + xc - tx / 2, yt + cy + offset))

        # Draw temp
        (ctx, cty) = c_temp.get_size()
        (htx, hty) = h_temp.get_size()
        self._screen.blit(temp_label, (xl + offset, yt + bo + cy + ty + text_border))
        self._screen.blit(c_temp, (lc - ctx / 2, yt + bo + cy + ty + text_border))
        self._screen.blit(h_temp, (rc - htx / 2, yt + bo + cy + ty + text_border))

        # Draw humidity
        (chx, chy) = c_humid.get_size()
        (hhx, hhy) = h_humid.get_size()
        self._screen.blit(humid_label, (xl + offset, yt + bo + cy + ty + cty + text_border))
        self._screen.blit(c_humid, (lc - chx / 2, yt + bo + cy + ty + cty + text_border))
        self._screen.blit(h_humid, (rc - hhx / 2, yt + bo + cy + ty + hty + text_border))

        # Draw Barometric Pressure
        (cbx, cby) = c_baro.get_size()
        (hbx, hby) = h_baro.get_size()
        self._screen.blit(baro_label, (xl + offset, yt + bo + cy + ty + cty + chy + text_border))
        self._screen.blit(c_baro, (lc - cbx / 2, yt + bo + cy + ty + cty + chy + text_border))
        self._screen.blit(h_baro, (rc - hbx / 2, yt + bo + cy + ty + hty + hhy + text_border))

        # Draw wind speed
        (cwsx, cwsy) = c_wind_speed.get_size()
        (hwsx, hwsy) = h_wind_speed.get_size()
        self._screen.blit(wind_label, (xl + offset, yt + bo + cy + ty + cty + chy + cby + text_border))
        self._screen.blit(c_wind_speed, (lc - cwsx / 2, yt + bo + cy + ty + cty + chy + cby + text_border))
        self._screen.blit(h_wind_speed, (rc - hwsx / 2, yt + bo + cy + ty + hty + hhy + hby + text_border))

        # Draw wind direction
        (cwdx, cwdy) = c_wind_direction.get_size()
        (hwdx, hwdy) = h_wind_direction.get_size()
        self._screen.blit(wind_dir_label, (xl + offset, yt + bo + cy + ty + cty + chy + cby + cwsy + text_border))
        self._screen.blit(c_wind_direction, (lc - cwdx / 2, yt + bo + cy + ty + cty + chy + cby + cwsy + text_border))
        self._screen.blit(h_wind_direction, (rc - hwdx / 2, yt + bo + cy + ty + hty + hhy + hby + hwsy + text_border))

        # Draw light index
        (clx, cly) = c_lumen.get_size()
        (hlx, hly) = h_lumen.get_size()
        self._screen.blit(li_label, (xl + offset, yt + bo + cy + ty + cty + chy + cby + cwsy + cwdy + text_border))
        self._screen.blit(c_lumen, (lc - clx / 2, yt + bo + cy + ty + cty + chy + cby + cwsy + cwdy + text_border))
        self._screen.blit(h_lumen, (rc - hlx / 2, yt + bo + cy + ty + hty + hhy + hby + hwsy + hwdy + text_border))

    def display_start(self):
        """display_start is the main initializer for the display it makes calls to many other
        internal functions in order do build the dispay as defined in the initialization of the
        DispayDriver class."""

        try:
            self.__get_driver()
            self.__draw_screen()

        except AssertionError as err:
            print(err)
            quit()

    def update_diplay(self):
        try:
            self.__draw_frames()
            self.__display_datetime()
            self.__display_connected()
            self.__display_connected()
            self.__display_forecasts()
            self.__weather_vane()
            self.__display_indoor()
            self.__display_left_frame()
            self.__display_sensor_detail_data()
            self.__display_feels_like()
            self.__render_screen()
            self.__display_wind_avg()
            pygame.display.update()
        except AssertionError as err:
            print("Update Error + {}".format(str(err)))

    def update_daily_data(self):
        self._system_data.forecasts.update_forecast_data()
        self._system_data.forecasts.update_forecasts()

    def update_current_data(self):
        self._system_data.ws.update_station()

    def run(self, run_delay=209):
        cnt = 0
        self.display_start()

        running = True
        while running:

            pygame.time.wait(1000)
            self.update_diplay()
            cnt += 1
            if cnt >= run_delay:
                cnt = 0
                self.update_current_data()
            if time.strftime("%d/%m") != self._system_data.current_date:
                self._system_data.current_date = time.strftime("%d/%m")
                self.update_daily_data()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
        pygame.quit()
