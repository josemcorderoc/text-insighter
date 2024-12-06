LOCALES := en es

# Target to compile all locales
all: $(LOCALES)

# Rule to compile a single locale
$(LOCALES):
	msgfmt locales/$@/LC_MESSAGES/messages.po -o locales/$@/LC_MESSAGES/messages.mo
	echo "Compiled locales/$@/LC_MESSAGES/messages.po to locales/$@/LC_MESSAGES/messages.mo"

# Clean target to remove all .mo files
clean:
	@for locale in $(LOCALES); do \
		rm -f locales/$$locale/LC_MESSAGES/messages.mo; \
		echo "Removed locales/$$locale/LC_MESSAGES/messages.mo"; \
	done

# Target to convert favicon
favicon:
	magick -background none assets/favicon.svg -resize 64x64 assets/favicon.ico
	echo "Converted assets/favicon.svg to assets/favicon.ico"

.PHONY: all clean $(LOCALES) favicon