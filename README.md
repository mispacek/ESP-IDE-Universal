
# ESP-IDE-Universal
 ESP IDE nová univerzální verze

Verze která obsahuje snáze udržitelný kód, který je kompatibilní s více druhy ESP
Projekt je rozdělen na 4 složky :

| Složka         |ASCII                                                    |HTML                         |
|----------------|---------------------------------------------------------|-----------------------------|
|Universal       |Univerzální kód který je společný pro všechny varianty   |Obsahuje main.py a celý webový interface            |
|ESP32           |kód který se liší od univerzálního            |toolbox.xml, příklady atp.            |
|ESP32C3         |kód který se liší od univerzálního            |toolbox.xml, příklady atp.            |
|ESP32S3         |kód který se liší od univerzálního            |toolbox.xml, příklady atp.            |

# Jak nahrát kód do ESP ?
můžete použít online instalátor na **https://espide.eu/**
nebo
použijte nástroj **Thonny** a do procesoru nakopírujte obsah složky universal + obsah složky podle názvu vašeho procesoru.

Poté procesor zrestartujte a měl by ze sebe vytvořit AP kde na adrese [192.168.4.1](http://192.168.4.1) najdete ESP IDE

Pokud chcete provést konfiguraci displeje nebo Wi-Fi můžete použít konfigurátor  https://espide.eu/instalace/conf.html kterým si nastavíte piny pro připojení I2C displeje a nastavíte si přístup na Wi-Fi


