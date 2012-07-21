﻿# Copyright 2004-2012 Tom Rothamel <pytom@bishoujo.us>
# See LICENSE.txt for license details.

init python:
    import random
    import codecs
    import re
    import sys

    def theme_names():
        """
        Gets a list of all of the theme names we know about.
        """
        
        names = list(theme_data.THEME.keys())
        names.sort(key=lambda a : a.lower())
        
        return names
    
    def scheme_names(theme):
        """
        Gets a list of the color scheme names corresponding to the given
        theme.
        """
        
        names = list(theme_data.THEME[theme].keys())
        names.sort(key=lambda a : a.lower())
        
        return names

    def theme_yinitial():
        names = theme_names()
        
        if len(names) < 2:
            return 0
            
        return 1.0 * names.index(current_theme) / (len(names) - 1)

    def scheme_yinitial():
        names = scheme_names(current_theme)
        
        if len(names) < 2:
            return 0
            
        return 1.0 * names.index(current_scheme) / (len(names) - 1)


    def pick_theme(theme, scheme):
        """
        Returns a theme and scheme that are similar to `theme` and `scheme`. 
        
        If the theme is known, picks it, otherwise picks a random theme. If
        the scheme is known for that theme, picks it, otherwise picks a 
        random scheme that is known for the current theme.
        """
        
        if theme not in theme_data.THEME:
            theme = random.choice(list(theme_data.THEME))
        
        schemes = theme_data.THEME[theme]
        
        if scheme not in schemes:
            if theme in schemes:
                scheme = theme
            else:
                scheme = random.choice(list(schemes))
            
        return theme, scheme
        
    def implement_theme(theme, scheme):
        global showing_theme, showing_scheme
        
        if theme == showing_theme and scheme == showing_scheme:
            return

        renpy.style.restore(style_backup)
        exec theme_data.THEME[theme][scheme] in globals()
        renpy.style.rebuild()

        showing_theme = theme
        showing_scheme = scheme

        renpy.restart_interaction()
    
    showing_theme = None
    showing_scheme = None

    class SetTheme(Action):
        def __init__(self, theme):
            self.theme = theme
            
        def __call__(self):
            global current_theme
            global current_scheme 
            
            current_theme, current_scheme = pick_theme(self.theme, current_scheme)
            
            implement_theme(current_theme, current_scheme)
            renpy.restart_interaction()

        def get_selected(self):
            return current_theme == self.theme
            
    class SetScheme(Action):
        def __init__(self, scheme):
            self.scheme = scheme
            
        def __call__(self):
            global current_theme
            global current_scheme 
            
            current_theme, current_scheme = pick_theme(current_theme, self.scheme)
            
            implement_theme(current_theme, current_scheme)
            renpy.restart_interaction()
            
        def get_selected(self):
            return current_scheme == self.scheme
            
    class PreviewTheme(Action):
        
        def __init__(self, theme, scheme):
            self.theme = theme
            self.scheme = scheme
            
        def __call__(self):
            theme, scheme = pick_theme(self.theme, self.scheme)
            implement_theme(theme, scheme)
            
        def unhovered(self):
            if (showing_theme == self.theme and showing_scheme == self.scheme):
                implement_theme(current_theme, current_scheme)

    def value_changed(value):
        return None

    ##########################################################################
    # Code to update options.rpy
    
    def list_logical_lines(filename):
        """
         This reads in filename, and turns it into a list of logical
         lines. 
        """

        f = codecs.open(filename, "rb", "utf-8")
        data = f.read()
        f.close()

        # The result.
        rv = [ ]

        # The current position we're looking at in the buffer.
        pos = 0

        # Looping over the lines in the file.
        while pos < len(data):

            # The line that we're building up.
            line = ""

           # The number of open parenthesis there are right now.
            parendepth = 0

            # Looping over the characters in a single logical line.
            while pos < len(data):

                c = data[pos]

                if c == '\n' and not parendepth:
                    rv.append(line)

                    pos += 1
                    # This helps out error checking.
                    line = ""
                    break

                # Backslash/newline.
                if c == "\\" and data[pos+1] == "\n":
                    pos += 2
                    line += "\\\n"
                    continue

                # Parenthesis.
                if c in ('(', '[', '{'):
                    parendepth += 1

                if c in ('}', ']', ')') and parendepth:
                    parendepth -= 1

                # Comments.
                if c == '#':
                    while data[pos] != '\n':
                        line += data[pos]
                        pos += 1

                    continue

                # Strings.
                if c in ('"', "'", "`"):
                    delim = c
                    line += c
                    pos += 1

                    escape = False

                    while pos < len(data):

                        c = data[pos]

                        if escape:
                            escape = False
                            pos += 1
                            line += c
                            continue

                        if c == delim:
                            pos += 1
                            line += c
                            break

                        if c == '\\':
                            escape = True

                        line += c
                        pos += 1

                        continue

                    continue
                    
                line += c
                pos += 1

        if line:
            rv.append(line)

        return rv


    def switch_theme():
        """
        Switches the theme of the current project to the current theme 
        and color scheme. (As set in current_theme and current_scheme.)
        """

        theme_code = theme_data.THEME[current_theme][current_scheme]

        # Did we change the file at all?
        changed = False

        filename = os.path.join(project.current.path, "game/options.rpy")

        with codecs.open(filename + ".new", "wb", "utf-8") as out:

            for l in list_logical_lines(filename):

                m = re.match(r'    theme.(\w+)\(', l)
                if (not changed) and m and (m.group(1) in theme_data.THEME_FUNCTIONS):
                    l = "    " + theme_code
                    changed = True
                        
                out.write(l + "\n")

        if changed:
            try:
                os.unlink(filename + ".bak")
            except:
                pass

            os.rename(filename, filename + ".bak")
            os.rename(filename + ".new", filename)
        else:
            os.unlink(filename + ".new")
            interface.error(_("Could not change the theme. Perhaps options.rpy was changed too much."))

init 100 python:
    style_backup = renpy.style.backup()


screen theme_demo:
    
    window:
        style "gm_root"
        xpadding 5
        ypadding 5

        grid 1 1:
            xfill True
            style_group "prefs"

            vbox:
                    
                frame:
                    style_group "pref"
                    has vbox
          
                    label _("Display")
                    textbutton _("Window") action SelectedIf(True)
                    textbutton _("Fullscreen") action ui.returns(None)
                    textbutton _("Planetarium") action None
                    

                frame:
                    style_group "pref"
                    has vbox

                    label _("Sound Volume")
                    bar value .75 range 1.0 changed value_changed

                    textbutton "Test":
                        action ui.returns(None)
                        style "soundtest_button"


init -2 python:
    style.pref_frame.xfill = True
    style.pref_frame.xmargin = 5
    style.pref_frame.top_margin = 5

    style.pref_vbox.xfill = True

    style.pref_button.size_group = "pref"
    style.pref_button.xalign = 1.0

    style.pref_slider.xmaximum = 192
    style.pref_slider.xalign = 1.0

    style.soundtest_button.xalign = 1.0


screen choose_theme:

    frame:
        style_group "l"
        style "l_root"
        
        window:
    
            has vbox

            label _("Choose Theme")

            hbox:
                yfill True
                
                # Theme selector.
                frame:
                    style "l_indent"
                    bottom_margin HALF_SPACER_HEIGHT
                    xmaximum 225

                    has vbox
                    
                    label _("Theme") style "l_label_small"

                    viewport:
                        scrollbars "vertical"
                        yinitial theme_yinitial()
                        mousewheel True
                        
                        has vbox
            
                        for i in theme_names():
                            textbutton "[i]":
                                action SetTheme(i)
                                hovered PreviewTheme(i, current_scheme)
                                style "l_list2" 

                
                # Color scheme selector.
                frame:
                    style "l_indent"
                    bottom_margin HALF_SPACER_HEIGHT
                    xmaximum 225
                    
                    has vbox
                    
                    label _("Color Scheme") style "l_label_small"
                    
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        yinitial scheme_yinitial()
                        
                        has vbox
            
                        for i in scheme_names(current_theme):
                            textbutton "[i]":  
                                action SetScheme(i)
                                hovered PreviewTheme(current_theme, i)
                                style "l_list2" 

                
                # Preview
                frame:
                    style "l_default"
                    background Frame("pattern.png", 0, 0, tile=True)
                    xpadding 5
                    ypadding 5

                    xfill True
                    yfill True
                    xmargin 20
                    bottom_margin 6
                
                    use theme_demo

    textbutton _("Back") action Jump("front_page") style "l_left_button"
    textbutton _("Continue") action Return(True) style "l_right_button"
                        

label choose_theme_callable:

    python:
        current_theme, current_scheme = pick_theme(None, None)
        implement_theme(current_theme, current_scheme) 
    
    call screen choose_theme

    python hide:
        with interface.error_handling("changing the theme"):
            switch_theme()

    return
    
label choose_theme:
    call choose_theme_callable
    jump front_page

    
