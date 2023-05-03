SECTIONS
{
  .text 0x0000 :
  {
    *(.text)
  }
  .data 0x1000 :
  {
    *(.data)
  }
  .bss 0x2000 :
  {
    *(.bss)
  }
}
