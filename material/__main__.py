from . import main, log

log.init()
try:
    main.material.main()
except KeyboardInterrupt:
    print("Material is OFF")
