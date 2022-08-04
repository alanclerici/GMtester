import machine
import utime as time
from machine import Pin, PWM
import micropython

class Display:
    
    
    def __init__(self, Pins, kind = 'C', transistor_pins = 1):
        self.kind = kind
        self.number_digit = len(transistor_pins)
        
        #Configura los pines del display como salida
        display = list()
        for i in range(7):
            display.append( Pin(Pins[i], Pin.OUT) )
        
        #Configura los pines de los transistores como salida
        transistors = list()
        for i in range(self.number_digit):
            transistors.append( Pin(transistor_pins[i], Pin.OUT) )
        
        #Tupla con las posiciones del display
        self.display = display
        
        #Tupla con las posiciones de los transistores
        self.transistors = transistors
        
    def show(self, digits):
        #Realiza la multiplexación
        flag=0
        global pin_punto
        
        if digits>=10000:
            digits=digits/10
            flag=1
                
        for i in range( self.number_digit ):
            number = int((digits % 10 ** (i+1)) / 10 ** i)
            self._show_one_display(number)
            if flag==0 and i==1:
                #pongo punto
                pin_punto.value(1)
            else:
                pin_punto.value(0)
            
            if not( (i==3 and digits<1000) or (i==2 and digits<100) ):
                self.transistors[i].on()
            time.sleep_ms(5)
            self.transistors[i].off()
                
    
    #Metodo probado para mostrar número en un solo display
    def _show_one_display(self, digit):
        bit = 1;
        
        #Display Cátodo Común
        if self.kind.upper() == 'C':
            numbers = (int('3f',16),int('06',16),int('5b',16),int('4f',16),int('66',16),int('6d',16),int('7d',16),int('07',16),int('7f',16),int('67',16))
        #Display Ánodo Común
        elif self.kind.upper() == 'A':
            numbers = (int('40',16),int('79',16),int('24',16),int('30',16),int('19',16),int('12',16),int('02',16),int('78',16),int('00',16),int('18',16))
        else:
            return
        
        for i in range(7):
            if (numbers[digit]  & bit) == 0:
                self.display[i].off()
            else:
                self.display[i].on()
            bit = bit << 1



class Rotary:
    
    ROT_CW = 1
    ROT_CCW = 2
    SW_PRESS = 4
    SW_RELEASE = 8
    
    def __init__(self,dt,clk,sw):
        self.dt_pin = Pin(dt, Pin.IN)
        self.clk_pin = Pin(clk, Pin.IN)
        self.sw_pin = Pin(sw, Pin.IN)
        self.last_status = (self.dt_pin.value() << 1) | self.clk_pin.value()
        self.dt_pin.irq(handler=self.rotary_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING )
        self.clk_pin.irq(handler=self.rotary_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING )
        self.sw_pin.irq(handler=self.switch_detect, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING )
        self.handlers = []
        self.last_button_status = self.sw_pin.value()
        
    def rotary_change(self, pin):
        new_status = (self.dt_pin.value() << 1) | self.clk_pin.value()
        if new_status == self.last_status:
            return
        transition = (self.last_status << 2) | new_status
        if transition == 0b1110:
            micropython.schedule(self.call_handlers, Rotary.ROT_CW)
        elif transition == 0b1101:
            micropython.schedule(self.call_handlers, Rotary.ROT_CCW)
        self.last_status = new_status
        
    def switch_detect(self,pin):
        if self.last_button_status == self.sw_pin.value():
            return
        self.last_button_status = self.sw_pin.value()
        if self.sw_pin.value():
            micropython.schedule(self.call_handlers, Rotary.SW_RELEASE)
        else:
            micropython.schedule(self.call_handlers, Rotary.SW_PRESS)
            
    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def call_handlers(self, type):
        for handler in self.handlers:
            handler(type)


def rotary_changed(change):
    global val

    if change == Rotary.ROT_CW:
        
        if val<100:
            val = val + 1
        elif val<1000:
            val = val + 10
        elif val<10000:
            val = val + 100
        else:
            val = val + 1000
        
        if val>50000:
            val=50000
        
        out.freq(val)
    elif change == Rotary.ROT_CCW:
        
        if val<=100:
            val = val - 1
        elif val<=1000:
            val = val - 10
        elif val<=10000:
            val = val - 100
        else:
            val = val - 1000
            
        if val<10:
            val=10
            
        out.freq(val)
    #print(val)


rotary = Rotary(0,1,2)
val = 10

rotary.add_handler(rotary_changed)

out = PWM(Pin(3))
out.duty_u16(32768)
out.freq(10)

display_pins = (16, 18, 13, 14, 15, 17, 12) #(a, b, c, d, e, f, g)
transistor_pins = (22, 21, 20, 19)
    
display7 = Display(display_pins,transistor_pins = transistor_pins )
pin_punto=Pin(11, Pin.OUT)



while True:
    display7.show(val)