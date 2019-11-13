#include <linux/build-salt.h>
#include <linux/module.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

BUILD_SALT;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__attribute__((section(".gnu.linkonce.this_module"))) = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif

static const struct modversion_info ____versions[]
__used
__attribute__((section("__versions"))) = {
	{ 0xf230cadf, "module_layout" },
	{ 0x309d9a5c, "usb_deregister" },
	{ 0x7c32d0f0, "printk" },
	{ 0xcf829e14, "put_tty_driver" },
	{ 0x74dbc48f, "tty_unregister_driver" },
	{ 0x8e42af5d, "usb_register_driver" },
	{ 0x61457efa, "tty_register_driver" },
	{ 0x85eb110, "tty_set_operations" },
	{ 0x67b27ec1, "tty_std_termios" },
	{ 0xff96246d, "__tty_alloc_driver" },
	{ 0xf82eda03, "tty_port_register_device" },
	{ 0x59bace72, "usb_get_intf" },
	{ 0xa9f5d8a8, "usb_driver_claim_interface" },
	{ 0xb59b06fc, "_dev_info" },
	{ 0x12da5bb2, "__kmalloc" },
	{ 0xb98d5724, "device_create_file" },
	{ 0x6cf6f88c, "_dev_warn" },
	{ 0x7fe179a5, "usb_alloc_urb" },
	{ 0xe3054914, "usb_alloc_coherent" },
	{ 0xfa4b7086, "tty_port_init" },
	{ 0xe346f67a, "__mutex_init" },
	{ 0xd0cd7b38, "usb_ifnum_to_if" },
	{ 0xc6cbbc89, "capable" },
	{ 0x28cc25db, "arm_copy_from_user" },
	{ 0xf4fa543b, "arm_copy_to_user" },
	{ 0x5f754e5a, "memset" },
	{ 0xbc10dd97, "__put_user_4" },
	{ 0x1e9a78cc, "kmem_cache_alloc_trace" },
	{ 0x51201dd7, "kmalloc_caches" },
	{ 0x353e3fa5, "__get_user_4" },
	{ 0x71c90087, "memcmp" },
	{ 0x409873e3, "tty_termios_baud_rate" },
	{ 0x2065fa1c, "tty_port_open" },
	{ 0xe707d823, "__aeabi_uidiv" },
	{ 0x7833eb5e, "usb_autopm_put_interface" },
	{ 0xd639e9f1, "usb_autopm_get_interface" },
	{ 0xdb7305a1, "__stack_chk_fail" },
	{ 0x8f678b07, "__stack_chk_guard" },
	{ 0x77b8ed2d, "tty_standard_install" },
	{ 0xce90062e, "refcount_inc_not_zero_checked" },
	{ 0x3e93f135, "tty_port_close" },
	{ 0x7548af95, "usb_autopm_get_interface_async" },
	{ 0x6e211d5f, "tty_port_hangup" },
	{ 0x5c675c78, "tty_port_tty_wakeup" },
	{ 0x37a0cba, "kfree" },
	{ 0x32cc7915, "usb_put_intf" },
	{ 0xcb08a872, "tty_insert_flip_string_fixed_flag" },
	{ 0xe5b11bc6, "tty_flip_buffer_push" },
	{ 0xae38fa9f, "__tty_insert_flip_char" },
	{ 0xb2d48a2e, "queue_work_on" },
	{ 0x2d3385d3, "system_wq" },
	{ 0x91715312, "sprintf" },
	{ 0x4faaf579, "tty_port_put" },
	{ 0xe7559896, "usb_driver_release_interface" },
	{ 0x4fcc824c, "usb_free_urb" },
	{ 0x3c446a29, "tty_unregister_device" },
	{ 0xa44a2b5b, "tty_kref_put" },
	{ 0x8101f7fd, "tty_vhangup" },
	{ 0x44ffb64e, "tty_port_tty_get" },
	{ 0x67ea780, "mutex_unlock" },
	{ 0x179d585d, "device_remove_file" },
	{ 0xc271c3be, "mutex_lock" },
	{ 0x5d7ec1d4, "usb_free_coherent" },
	{ 0xdb9ca3c5, "_raw_spin_lock" },
	{ 0x4205ad24, "cancel_work_sync" },
	{ 0x480e4f2b, "usb_kill_urb" },
	{ 0x676bbc0f, "_set_bit" },
	{ 0x2a3aa678, "_test_and_clear_bit" },
	{ 0xd697e69a, "trace_hardirqs_on" },
	{ 0x2da81bff, "_raw_spin_lock_irq" },
	{ 0x5b99cfc0, "usb_autopm_put_interface_async" },
	{ 0xc4358a27, "tty_port_tty_hangup" },
	{ 0x5ade57f0, "_dev_err" },
	{ 0x52bfd9e8, "usb_submit_urb" },
	{ 0x526c3a6c, "jiffies" },
	{ 0x9d669763, "memcpy" },
	{ 0x7bdd27c3, "dev_printk" },
	{ 0x8157e73e, "usb_control_msg" },
	{ 0x2e5810c6, "__aeabi_unwind_cpp_pr1" },
	{ 0x39a12ca7, "_raw_spin_unlock_irqrestore" },
	{ 0x5f849a69, "_raw_spin_lock_irqsave" },
	{ 0xb1ad28e0, "__gnu_mcount_nc" },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=";

MODULE_ALIAS("usb:v04E2p1410d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1411d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1412d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1414d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1420d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1421d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1422d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1424d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1400d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1401d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1402d*dc*dsc*dp*ic*isc*ip*in*");
MODULE_ALIAS("usb:v04E2p1403d*dc*dsc*dp*ic*isc*ip*in*");

MODULE_INFO(srcversion, "46A7F92CA664A90B1604A1E");
